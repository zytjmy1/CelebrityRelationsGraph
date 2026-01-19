🎭 Celebrity Relations Graph<p align="center"><img src="https://www.google.com/search?q=https://img.shields.io/badge/Python-3.8%2B-blue.svg" alt="Python"><img src="https://www.google.com/search?q=https://img.shields.io/badge/LLM-GPT--4%2520|%20Qwen-orange.svg" alt="LLM"><img src="https://www.google.com/search?q=https://img.shields.io/badge/Framework-Flask-lightgrey.svg" alt="Framework"><img src="https://www.google.com/search?q=https://img.shields.io/badge/License-MIT-green.svg" alt="License"><img src="https://www.google.com/search?q=https://img.shields.io/badge/PRs-Welcome-brightgreen.svg" alt="PRs Welcome"></p><p align="center"><strong>An automated pipeline to extract and visualize social networks using LLMs and BFS.</strong></p>English | 中文文档<a name="english"></a>🌟 OverviewCelebrity Relations Graph is an intelligent OSINT tool designed to map the intricate social networks of public figures. By leveraging Large Language Models (LLM) for entity-relation extraction and Breadth-First Search (BFS) for multi-hop discovery, it transforms unstructured Wikipedia biographies into high-fidelity, interactive knowledge graphs.
    - Watch the live logs as the graph builds!

## Recently Updated Technologies

### 1. Multi-Source Search Fallback
- **DuckDuckGo Integration**: If Wikipedia extraction fails (e.g., page not found), the system automatically performs a web search using `duckduckgo-search` to gather biography snippets.
- **Robustness**: Ensures graph generation even for niche celebrities or when direct URLs fail.

### 2. Intelligent Error Handling
- **Content Filter Bypass**: Automatically detects AI content policy violations (Error 400) and switches to safer fallback data sources.
- **User Feedback**: clearer error messages in the UI when no data is available after all attempts.

### 3. Visual Intimacy Engine
- **Thickened Connections**: Edges now dynamically scale in thickness (1px - 9px) based on the intimacy score (1-10).
- **Physics Tuning**: Closer relationships are physically pulled tighter together in the graph layout for immediate visual hierarchy.
🚀 Key FeaturesIntelligent Extraction: Deeply parses unstructured text to identify (Subject, Predicate, Object) triplets using state-of-the-art LLMs.Intimacy Scoring: A proprietary LLM-driven heuristic (scale 1-10) to quantify relationship closeness (e.g., Family: 10, Acquaintance: 2).Dynamic Crawler: Supports multi-hop depth (Fast vs. Deep) to uncover the "Network behind the Network."Glassmorphism UI: A modern, physics-based visualization dashboard featuring real-time Server-Sent Events (SSE) log streaming.🏗️ Technical ArchitectureThe system follows a modular design pattern to ensure scalability and extraction accuracy:graph TD
    A[User Input: Name] --> B[Wikipedia Scraper]
    B --> C{Extraction Mode}
    C -- Fast --> D[LLM Extraction Depth 1]
    C -- Deep --> E[BFS Recursive Crawler Depth 2]
    D --> F[Intimacy Scoring Engine]
    E --> F
    F --> G[NetworkX Topology]
    G --> H[Pyvis Interactive Graph]
    H --> I[Modern Web UI]
    style I fill:#f9f,stroke:#333,stroke-width:2px
📊 Mode ComparisonFeatureFast Mode (Depth 1)Deep Mode (Depth 2)Search ScopeTarget individual onlyTarget + Top-tier connectionsLLM WorkloadLow (~1-2 calls)High (N+1 recursive calls)DiscoveryDirect relatives & colleaguesHidden links & "Friends of friends"VisualizationStar-shaped topologyComplex social webLatencyInstant (< 10s)Sequential (30s - 2min)🔧 Getting Started1. Installationgit clone [https://github.com/your-username/celebrity-relations-graph.git](https://github.com/your-username/celebrity-relations-graph.git)
cd celebrity-relations-graph
pip install -r requirements.txt
2. ConfigurationCreate a .env file in the root directory:OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=[https://api.openai.com/v1](https://api.openai.com/v1)
3. Executionpython src/app.py
Visit http://localhost:8000 to start exploring.<a name="chinese"></a>🌟 项目简介Celebrity Relations Graph 是一款自动化的人际关系绘图工具。它结合了 大语言模型 (LLM) 的语义理解能力与 广度优先搜索 (BFS) 的路径发现算法，能将维基百科中杂乱的传记文本转化为高精度、可交互的社交知识图谱。🚀 核心特性智能关系提取：利用大模型深度解析非结构化文本，精准识别 (主体, 关系, 客体) 三元组。亲密度评分机制：通过 LLM 启发式算法为每条关系打分（1-10），直观量化人脉连接的紧密程度。多级爬虫引擎：提供“极速”与“深度”两种模式，支持跨层级挖掘“朋友圈后的朋友圈”。实时处理流：基于 SSE 技术，后端提取进度毫秒级同步至前端 UI。🏗️ 技术架构系统采用解耦的模块化设计，确保提取精度与系统稳定性：Scraper 层：高效率抓取 Wikipedia 摘要及人物生平数据。LLM 逻辑层：提示词工程驱动的结构化提取，兼容 GPT-4、Qwen、DeepSeek 等主流模型。拓扑层：利用 NetworkX 进行图论计算，处理节点冲突与去重。可视化层：Pyvis 物理引擎驱动，配合现代 玻璃拟态 (Glassmorphism) UI。📜 开源协议本项目基于 MIT License 协议开源。<p align="center"> Designed with ❤️ for the OSINT Community </p>