# 🎭 名人关系图谱 / Celebrity Relations Graph

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/LLM-OpenAI%20|%20Qwen-orange.svg" alt="LLM">
  <img src="https://img.shields.io/badge/Framework-Flask-lightgrey.svg" alt="Framework">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

<p align="center">
  <strong>利用大语言模型和广度优先搜索自动提取并可视化社交网络的 OSINT 工具</strong>
</p>

<div align="center">
  <button onclick="showEnglish()">English</button>
  <button onclick="showChinese()">中文</button>
</div>

<script>
function showEnglish() {
  document.getElementById('english').style.display = 'block';
  document.getElementById('chinese').style.display = 'none';
}
function showChinese() {
  document.getElementById('english').style.display = 'none';
  document.getElementById('chinese').style.display = 'block';
}
// 默认显示中文
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('chinese').style.display = 'block';
  document.getElementById('english').style.display = 'none';
});
</script>

<div id="chinese">

---

## 🌟 项目概述

**名人关系图谱** 是一个智能分析管道，专门用于绘制公众人物复杂的社交网络关系。它利用**大型语言模型（LLM）**进行实体-关系抽取，并结合**广度优先搜索（BFS）**实现多跳关系发现，将非结构化的维基百科或其他传记文本转化为高质量、可交互的知识图谱。

本工具超越了简单的关键词匹配，能够通过 AI 理解关系的**细微差别**与**亲密度**。

## 🚀 核心功能

- **🧠 智能关系抽取**：使用最先进的 LLM 深度解析文本，提取 `(主体, 关系, 对象)` 三元组
- **❤️ 亲密度评分**：专有 LLM 启发式打分（1-10 分），量化关系亲密度（家人：10 / 熟人：2）
- **🕸️ 动态多跳爬取**：支持“快速模式”（1跳）与“深度模式”（2跳），挖掘“网络背后的网络”
- **🎨 玻璃态交互界面**：基于物理引擎的现代化可视化仪表盘 + 实时日志流

## 🆕 近期技术更新

### 1. 多源搜索回退机制
- **DuckDuckGo 集成**：当 Wikipedia 页面不存在或提取失败时，自动切换到 duckduckgo-search 获取传记片段
- **鲁棒性提升**：即使小众名人或 URL 失效，也能尽量生成关系图

### 2. 智能错误处理
- **内容策略绕过**：自动识别 OpenAI 400 错误（内容违规），切换到更安全的备用数据源
- **用户友好提示**：所有尝试失败后在界面显示清晰的错误信息

### 3. 视觉亲密度引擎
- **动态边粗细**：根据亲密度分数（1-10）将连线厚度从 1px 渐变到 9px
- **物理布局优化**：亲密关系在力导向布局中被拉得更近，形成自然的视觉层级

## 🏗️ 技术架构

```mermaid
graph TD
    A[用户输入：姓名] --> B[Wikipedia / 搜索抓取]
    B --> C{提取模式}
    C -- 快速 --> D[LLM 单层抽取]
    C -- 深度 --> E[BFS 递归多跳爬取]
    D --> F[亲密度评分引擎]
    E --> F
    F --> G[NetworkX 图结构]
    G --> H[Pyvis 交互可视化]
    H --> I[现代化 Web 界面]
    style I fill:#f9f,stroke:#333,stroke-width:2px