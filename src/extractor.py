"""LLM-assisted, evidence-first relationship extraction."""

import json
import os
import re
from typing import Iterable

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MAX_SOURCE_CHARS = 11_000


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL"), timeout=120.0)


def _response_items(content: str) -> list[dict]:
    """Accept the common object wrapper and recover gracefully from fenced JSON."""
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", (content or "").strip())
    parsed = json.loads(content)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return parsed.get("relationships", parsed.get("items", []))
    return []


def _display_name(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_relationships(items: Iterable[dict], subject_name: str) -> list[tuple[str, str, str, int]]:
    """Validate model output and retain the strongest version of each directed fact."""
    subject = _display_name(subject_name)
    unique: dict[tuple[str, str, str], tuple[str, str, str, int]] = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        target = _display_name(item.get("target"))
        relation = _display_name(item.get("relation")).rstrip(".")
        if not target or not relation or target.casefold() == subject.casefold():
            continue
        if len(target) > 100 or len(relation) > 80:
            continue
        try:
            intimacy = max(1, min(10, int(item.get("intimacy", 5))))
        except (TypeError, ValueError):
            intimacy = 5
        key = (subject.casefold(), target.casefold(), relation.casefold())
        current = unique.get(key)
        candidate = (subject, target, relation, intimacy)
        if not current or candidate[3] > current[3]:
            unique[key] = candidate

    return sorted(unique.values(), key=lambda value: (-value[3], value[1].casefold()))[:20]


def extract_relationships(text: str, subject_name: str) -> list[tuple[str, str, str, int]]:
    """Extract only relationships that are directly supported by retrieved source text."""
    client = get_client()
    if not client:
        print("Warning: OPENAI_API_KEY not found. Skipping relationship extraction.")
        return []

    language = os.getenv("DEFAULT_LANGUAGE", "en")
    language_instruction = "Write relation labels in Simplified Chinese." if language == "zh" else "Write relation labels in English."
    subject = _display_name(subject_name)
    prompt = f"""
You extract a factual people-relationship graph from the source text below.

Subject: {subject}
Rules:
1. Return only direct relationships involving the Subject and a specifically named person.
2. Every relationship must be explicitly supported by the supplied source. Do not infer, guess, or use outside knowledge.
3. Prefer notable people, but retain a named spouse, parent, child, sibling, partner, or collaborator when directly stated.
4. Use a precise, short relation label; do not include dates, hedges, or duplicate facts.
5. Score intimacy from 1 to 10: immediate family/spouse 9-10; close creative or business partner 6-8; professional peer 3-5; brief association 1-2.
6. {language_instruction}

Return one JSON object only: {{"relationships": [{{"target": "person name", "relation": "short label", "intimacy": 1}}]}}.
Return at most 15 relationships.

Source:
{text[:MAX_SOURCE_CHARS]}
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "deepseek-chat"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": "You are a careful information-extraction system. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        return normalize_relationships(_response_items(response.choices[0].message.content), subject)
    except Exception as error:
        error_text = str(error).lower()
        if "data_inspection_failed" in error_text or "content filter" in error_text:
            raise ValueError("Content Blocked") from error
        print(f"Error extracting relationships: {error}")
        return []


if __name__ == "__main__":
    sample = [{"target": "Travis Kelce", "relation": "dated", "intimacy": 8}]
    print(normalize_relationships(sample, "Taylor Swift"))
