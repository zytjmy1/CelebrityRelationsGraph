from collections import deque
import json
import os
import re
import time

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from extractor import extract_relationships
from graph import create_graph, visualize_graph
from scraper import clean_query, find_celebrity_info

app = Flask(__name__)
OUTPUT_DIR = os.path.join(app.root_path, "static", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

RELATION_PRIORITY = {
    "妻": 10, "夫": 10, "配偶": 10, "父": 10, "母": 10, "子": 10, "女": 10, "兄": 9, "弟": 9, "姐": 9,
    "spouse": 10, "married": 10, "parent": 10, "father": 10, "mother": 10, "child": 10, "sibling": 9,
    "partner": 8, "collaborat": 7, "合作": 7, "搭档": 7, "band": 6, "co-star": 5,
}

MESSAGES = {
    "zh": {
        "name_required": "请输入人物姓名。",
        "invalid_mode": "不支持的搜索模式。",
        "invalid_language": "不支持的界面语言。",
        "starting": "正在解析人物：{name}",
        "wait_estimate": "预计等待约 {seconds} 秒，请保持页面开启。",
        "deep_enabled": "深度模式已开启：最多扩展两层关系网络。",
        "processing": "检索 {name} · 第 {depth} 层",
        "not_found": "未找到“{name}”的可靠公开资料，请尝试全名或常用英文名。",
        "skipped": "跳过 {name}：没有可用公开资料。",
        "matched": "已匹配到人物条目：{name}（{source}）。",
        "source": "已获取资料来源：{source}。",
        "extracting": "正在从 {name} 的资料中提取关系，预计还需约 {seconds} 秒…",
        "filtered_content": "该资料触发内容过滤，已跳过该条资料。",
        "no_relationships": "{name}：没有提取到可验证的人物关系。",
        "found": "{name}：找到 {count} 条关系。",
        "filtered_cycles": "已过滤 {count} 条回指或重复关系，避免无效回路。",
        "rendering": "正在生成交互式关系图…",
        "empty": "没有找到可验证的关系。可以尝试更明确的人物名称，或切换到深度模式。",
        "failed": "生成失败：{error}",
    },
    "en": {
        "name_required": "Enter a person's name.",
        "invalid_mode": "Unsupported search mode.",
        "invalid_language": "Unsupported interface language.",
        "starting": "Resolving profile: {name}",
        "wait_estimate": "Estimated wait: about {seconds} seconds. Please keep this page open.",
        "deep_enabled": "Deep mode enabled: exploring up to two relationship hops.",
        "processing": "Searching {name} · hop {depth}",
        "not_found": "No reliable public profile found for “{name}”. Try a full or common English name.",
        "skipped": "Skipped {name}: no public profile available.",
        "matched": "Matched profile: {name} ({source}).",
        "source": "Source loaded: {source}.",
        "extracting": "Extracting relationships from {name}'s profile — about {seconds} seconds remaining…",
        "filtered_content": "This profile triggered a content filter and was skipped.",
        "no_relationships": "{name}: no verifiable relationships found.",
        "found": "{name}: found {count} relationships.",
        "filtered_cycles": "Filtered {count} back-links or duplicate relationships to avoid loops.",
        "rendering": "Rendering interactive relationship graph…",
        "empty": "No verifiable relationships found. Try a more specific name or Deep mode.",
        "failed": "Generation failed: {error}",
    },
}


def stream_event(event_type: str, **payload):
    return json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n"


def message(language, key, **values):
    return MESSAGES[language][key].format(**values)


def relationship_score(relationship):
    relation = relationship[2].casefold()
    semantic_score = max((weight for keyword, weight in RELATION_PRIORITY.items() if keyword in relation), default=0)
    return semantic_score * 20 + relationship[3]


def person_key(name):
    """Create a tolerant identifier for comparing person names across sources."""
    return re.sub(r"[\s·•・'’`\".,，、()（）_\-]+", "", str(name or "")).casefold()


def keep_tree_relationships(relationships, depth, known_depths, root_keys):
    """Keep only the first shortest path to each person in a deep-search graph.

    This deliberately turns the exploration result into a tree: a person already
    discovered from an earlier hop cannot point back to the root or form a
    cross-link/cycle from a later hop.
    """
    kept = []
    dropped = 0
    targets_first_seen_here = set()

    for relationship in relationships:
        target_key = person_key(relationship[1])
        if not target_key or target_key in root_keys:
            dropped += 1
            continue

        known_depth = known_depths.get(target_key)
        if depth > 0 and known_depth is not None and target_key not in targets_first_seen_here:
            dropped += 1
            continue

        kept.append(relationship)
        if known_depth is None:
            known_depths[target_key] = depth + 1
            targets_first_seen_here.add(target_key)
        elif depth == 0:
            # Multiple root relationships to the same person are meaningful,
            # but the person still keeps its original shortest depth.
            targets_first_seen_here.add(target_key)

    return kept, dropped


def merge_relationships(relationships):
    """De-duplicate graph facts found from different article hops."""
    merged = {}
    for source, target, relation, intimacy in relationships:
        key = (source.casefold(), target.casefold(), relation.casefold())
        candidate = (source, target, relation, intimacy)
        if key not in merged or candidate[3] > merged[key][3]:
            merged[key] = candidate
    return sorted(merged.values(), key=lambda value: (-value[3], value[0].casefold(), value[1].casefold()))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    root_name = clean_query(data.get("name"))
    search_mode = data.get("mode", "fast")
    language = data.get("language", "zh")
    if not root_name:
        return jsonify({"error": message(language if language in MESSAGES else "zh", "name_required")}), 400
    if search_mode not in {"fast", "deep"}:
        return jsonify({"error": message(language if language in MESSAGES else "zh", "invalid_mode")}), 400
    if language not in MESSAGES:
        return jsonify({"error": message("zh", "invalid_language")}), 400

    def generate_stream():
        try:
            max_depth = 2 if search_mode == "deep" else 1
            branch_factor = 5 if search_mode == "deep" else 0
            estimated_seconds = 45 if search_mode == "deep" else 15
            queue = deque([(root_name, 0)])
            visited = set()
            known_depths = {person_key(root_name): 0}
            root_keys = {person_key(root_name)}
            all_relationships = []
            resolved_root = root_name
            source_summary = ""

            yield stream_event("log", message=message(language, "starting", name=root_name))
            yield stream_event("log", message=message(language, "wait_estimate", seconds=estimated_seconds))
            if search_mode == "deep":
                yield stream_event("log", message=message(language, "deep_enabled"))

            while queue:
                current_name, depth = queue.popleft()
                normalized = person_key(current_name)
                if normalized in visited:
                    continue
                visited.add(normalized)
                yield stream_event("log", message=message(language, "processing", name=current_name, depth=depth + 1))

                profile = find_celebrity_info(current_name)
                if not profile:
                    if depth == 0:
                        yield stream_event("error", message=message(language, "not_found", name=current_name))
                        return
                    yield stream_event("log", message=message(language, "skipped", name=current_name))
                    continue

                if depth == 0:
                    resolved_root = profile.name
                    source_summary = profile.source
                    root_keys.add(person_key(profile.name))
                    known_depths[person_key(profile.name)] = 0
                    if profile.name.casefold() != root_name.casefold():
                        yield stream_event("log", message=message(language, "matched", name=profile.name, source=profile.source))
                    else:
                        yield stream_event("log", message=message(language, "source", source=profile.source))

                yield stream_event(
                    "log",
                    message=message(language, "extracting", name=profile.name, seconds=estimated_seconds),
                )
                try:
                    relationships = extract_relationships(profile.text, profile.name, language=language)
                except ValueError:
                    yield stream_event("log", message=message(language, "filtered_content"))
                    relationships = []

                relationships, dropped = keep_tree_relationships(
                    relationships, depth, known_depths, root_keys
                )
                if not relationships:
                    if dropped:
                        yield stream_event("log", message=message(language, "filtered_cycles", count=dropped))
                    yield stream_event("log", message=message(language, "no_relationships", name=profile.name))
                    continue

                all_relationships.extend(relationships)
                yield stream_event("log", message=message(language, "found", name=profile.name, count=len(relationships)))
                if dropped:
                    yield stream_event("log", message=message(language, "filtered_cycles", count=dropped))

                if depth + 1 < max_depth:
                    next_people = []
                    for relationship in sorted(relationships, key=relationship_score, reverse=True):
                        target = relationship[1]
                        if person_key(target) not in visited and target not in next_people:
                            next_people.append(target)
                    for target in next_people[:branch_factor]:
                        queue.append((target, depth + 1))

            relationships = merge_relationships(all_relationships)
            if not relationships:
                yield stream_event("error", message=message(language, "empty"))
                return

            yield stream_event("log", message=message(language, "rendering"))
            filename_root = re.sub(r"[^\w\-]+", "_", resolved_root, flags=re.UNICODE).strip("_") or "graph"
            filename = f"{filename_root}_{int(time.time())}.html"
            output_path = os.path.join(OUTPUT_DIR, filename)
            graph = create_graph(relationships, root_name=resolved_root)
            visualize_graph(graph, output_path)
            yield stream_event(
                "result",
                graph_url=f"/static/output/{filename}",
                stats={"people": graph.number_of_nodes(), "relations": graph.number_of_edges()},
                source=source_summary,
                resolved_name=resolved_root,
            )
        except Exception as error:
            app.logger.exception("Graph generation failed")
            yield stream_event("error", message=message(language, "failed", error=error))

    return Response(stream_with_context(generate_stream()), content_type="application/x-ndjson; charset=utf-8")


if __name__ == "__main__":
    app.run(debug=True, port=8000)
