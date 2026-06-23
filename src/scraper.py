"""Reliable, language-aware public-profile retrieval."""

from dataclasses import dataclass
import re
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


WIKIPEDIA_API = "https://{language}.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": "CelebrityRelationsGraph/1.0 (public-profile research; contact: github.com/zytjmy1)"
}
REQUEST_TIMEOUT = 12


@dataclass
class CelebrityProfile:
    name: str
    text: str
    source: str
    url: str


def _languages_for(name: str) -> list[str]:
    """Search the most likely Wikipedia first, then fall back to the other one."""
    has_cjk = bool(re.search(r"[\u3400-\u9fff]", name))
    return ["zh", "en"] if has_cjk else ["en", "zh"]


def _request(params: dict, language: str) -> Optional[dict]:
    try:
        response = requests.get(
            WIKIPEDIA_API.format(language=language),
            params={"format": "json", "formatversion": 2, **params},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as error:
        print(f"Wikipedia request failed: {error}")
        return None


def _search_wikipedia(name: str, language: str) -> Optional[dict]:
    data = _request(
        {
            "action": "query",
            "list": "search",
            "srsearch": name,
            "srlimit": 5,
            "srnamespace": 0,
        },
        language,
    )
    results = (data or {}).get("query", {}).get("search", [])
    if not results:
        return None

    normalized = name.casefold().replace(" ", "")
    # Prefer an exact title, while retaining a useful first result for aliases.
    return next(
        (item for item in results if item["title"].casefold().replace(" ", "") == normalized),
        results[0],
    )


def _extract_wikipedia(title: str, language: str) -> Optional[CelebrityProfile]:
    data = _request(
        {
            "action": "query",
            "prop": "extracts|info",
            "titles": title,
            "redirects": 1,
            "inprop": "url",
            "explaintext": 1,
            "exsectionformat": "plain",
        },
        language,
    )
    pages = (data or {}).get("query", {}).get("pages", [])
    if not pages:
        return None

    page = pages[0]
    text = clean_text(page.get("extract", ""))
    if page.get("missing") or len(text) < 180 or "may refer to:" in text[:300].lower():
        return None

    return CelebrityProfile(
        name=page.get("title", title),
        text=text,
        source=f"{language}.wikipedia.org",
        url=page.get("fullurl", ""),
    )


def _direct_article(name: str, language: str) -> Optional[CelebrityProfile]:
    """A non-API fallback for when the public API is temporarily rate-limited."""
    url = f"https://{language}.wikipedia.org/wiki/{quote(name.replace(' ', '_'))}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    content = soup.find(id="mw-content-text")
    if not content:
        return None
    text = clean_text(" ".join(item.get_text(" ", strip=True) for item in content.find_all("p")))
    if len(text) < 180 or "may refer to:" in text[:300].lower():
        return None
    heading = soup.find(id="firstHeading")
    return CelebrityProfile(
        name=heading.get_text(strip=True) if heading else name,
        text=text,
        source=f"{language}.wikipedia.org",
        url=url,
    )


def find_celebrity_info(name: str) -> Optional[CelebrityProfile]:
    """Resolve a name through Wikipedia search rather than guessing an article URL."""
    query = clean_query(name)
    if not query:
        return None

    for language in _languages_for(query):
        result = _search_wikipedia(query, language)
        profile = _extract_wikipedia(result["title"], language) if result else None
        profile = profile or _direct_article(query, language)
        if profile:
            return profile

    fallback_text = search_fallback(query)
    if fallback_text:
        return CelebrityProfile(query, fallback_text, "web search", "")
    return None


def get_celebrity_info(name: str) -> Optional[str]:
    """Backward-compatible text-only API used by the CLI entry point."""
    profile = find_celebrity_info(name)
    return profile.text if profile else None


def search_fallback(name: str) -> Optional[str]:
    """Collect a small, clearly marked search fallback when Wikipedia has no article."""
    try:
        from duckduckgo_search import DDGS

        results = DDGS().text(f'"{name}" biography relationships', max_results=5)
        snippets = []
        for result in results or []:
            title, body = result.get("title", ""), result.get("body", "")
            if title and body:
                snippets.append(f"{title}\n{body}")
        if snippets:
            return "[FALLBACK SEARCH RESULT]\n" + "\n\n".join(snippets)
    except Exception as error:
        print(f"Fallback search error: {error}")
    return None


def clean_query(name: str) -> str:
    return re.sub(r"\s+", " ", str(name or "")).strip()[:120]


def clean_text(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


if __name__ == "__main__":
    profile = find_celebrity_info("Taylor Swift")
    print(f"Found {profile.name if profile else 'nothing'}")
