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


def stream_event(event_type: str, **payload):
    return json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n"


def relationship_score(relationship):
    relation = relationship[2].casefold()
    semantic_score = max((weight for keyword, weight in RELATION_PRIORITY.items() if keyword in relation), default=0)
    return semantic_score * 20 + relationship[3]


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
    if not root_name:
        return jsonify({"error": "请输入人物姓名。"}), 400
    if search_mode not in {"fast", "deep"}:
        return jsonify({"error": "不支持的搜索模式。"}), 400

    def generate_stream():
        try:
            max_depth = 2 if search_mode == "deep" else 1
            branch_factor = 5 if search_mode == "deep" else 0
            queue = deque([(root_name, 0)])
            visited = set()
            all_relationships = []
            resolved_root = root_name
            source_summary = ""

            yield stream_event("log", message=f"正在解析人物：{root_name}")
            if search_mode == "deep":
                yield stream_event("log", message="深度模式已开启：最多扩展两层关系网络。")

            while queue:
                current_name, depth = queue.popleft()
                normalized = re.sub(r"\s+", " ", current_name).casefold()
                if normalized in visited:
                    continue
                visited.add(normalized)
                yield stream_event("log", message=f"检索 {current_name} · 第 {depth + 1} 层")

                profile = find_celebrity_info(current_name)
                if not profile:
                    if depth == 0:
                        yield stream_event("error", message=f"未找到“{current_name}”的可靠公开资料，请尝试全名或常用英文名。")
                        return
                    yield stream_event("log", message=f"跳过 {current_name}：没有可用公开资料。")
                    continue

                if depth == 0:
                    resolved_root = profile.name
                    source_summary = profile.source
                    if profile.name.casefold() != root_name.casefold():
                        yield stream_event("log", message=f"已匹配到人物条目：{profile.name}（{profile.source}）。")
                    else:
                        yield stream_event("log", message=f"已获取资料来源：{profile.source}。")

                yield stream_event("log", message=f"正在从 {profile.name} 的资料中提取关系…")
                try:
                    relationships = extract_relationships(profile.text, profile.name)
                except ValueError:
                    yield stream_event("log", message="该资料触发内容过滤，已跳过该条资料。")
                    relationships = []

                if not relationships:
                    yield stream_event("log", message=f"{profile.name}：没有提取到可验证的人物关系。")
                    continue

                all_relationships.extend(relationships)
                yield stream_event("log", message=f"{profile.name}：找到 {len(relationships)} 条关系。")

                if depth + 1 < max_depth:
                    next_people = []
                    for relationship in sorted(relationships, key=relationship_score, reverse=True):
                        target = relationship[1]
                        if target.casefold() not in visited and target not in next_people:
                            next_people.append(target)
                    for target in next_people[:branch_factor]:
                        queue.append((target, depth + 1))

            relationships = merge_relationships(all_relationships)
            if not relationships:
                yield stream_event("error", message="没有找到可验证的关系。可以尝试更明确的人物名称，或切换到深度模式。")
                return

            yield stream_event("log", message="正在生成交互式关系图…")
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
            yield stream_event("error", message=f"生成失败：{error}")

    return Response(stream_with_context(generate_stream()), content_type="application/x-ndjson; charset=utf-8")


if __name__ == "__main__":
    app.run(debug=True, port=8000)
