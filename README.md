# AI Daily - 智能科技日报生成器

基于 **FastAPI + DeepSeek** 的自动化科技日报服务：从国内多源 RSS 抓取科技新闻 → 智能去重 → 调用 DeepSeek 生成结构化中文日报 → 提供极简网页展示与 Markdown 下载。

---

## ✨ 功能特性

- **国内多源新闻抓取**：从 36氪、少数派、虎嗅、极客公园、IT之家 等 RSS 源拉取最新科技新闻  
- **智能去重**：基于标题相似度自动剔除重复/高度相似新闻  
- **AI 日报生成**：使用 DeepSeek `deepseek-chat` 生成结构化日报正文 + 3 个公众号风格标题  
- **同日缓存**：同一天内优先返回缓存，可选 `force_refresh` 强制重新抓取并生成  
- **极简网页首页**：访问 `/` 即可查看今日日报（Markdown 渲染）、刷新、重新生成、下载 Markdown  
- **RESTful API**：`/daily`（JSON）、`/daily.md`（Markdown 下载）、`/health`、`/docs`  

---

## 📁 项目结构

```
ai-daily/
├── app.py              # FastAPI 入口：/、/daily、/daily.md、/health
├── fetch_news.py       # 新闻抓取（国内 RSS 源）
├── deduplicate.py      # 新闻去重（标题相似度）
├── generate_daily.py   # 日报生成与缓存（DeepSeek）
├── prompt.py           # 日报 Prompt 模板
├── requirements.txt    # 项目依赖
├── data/               # 自动创建
│   ├── news.json       # 最近一次抓取的原始新闻（调试用）
│   └── daily_YYYY-MM-DD.json  # 当日日报缓存
├── .env                # 需自建，配置 DEEPSEEK_API_KEY
└── README.md
```

---

## 🧠 整体流程

1. **抓取新闻**：`fetch_news(limit=30)` 从多个国内 RSS 源拉取新闻（标题、摘要、链接）  
2. **去重**：`deduplicate_news(raw_news, threshold=0.8)` 按标题相似度过滤  
3. **生成日报**：`generate_daily(news_list, force_refresh=…)`  
   - 若当日已有缓存且未传 `force_refresh=True`，直接返回缓存  
   - 否则调用 DeepSeek 生成日报正文与标题，并写入 `data/daily_YYYY-MM-DD.json`  
4. **展示 / 下载**：网页 `/` 展示（Markdown 渲染），`/daily.md` 返回纯 Markdown 供下载  

---

## 🛠️ 安装与配置

### 环境要求

- Python 3.8+  
- [DeepSeek API Key](https://platform.deepseek.com/)（写入 `.env`）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 .env

在项目根目录创建 `.env`：

```env
DEEPSEEK_API_KEY=你的_deepseek_api_key
```

`app.py` 与 `generate_daily.py` 通过 `python-dotenv` 加载，未配置时会报错提示。

---

## 🚀 运行与使用

### 启动服务

```bash
uvicorn app:app --reload
```

默认地址：**http://localhost:8000**

### 网页首页（推荐）

- 打开 **http://localhost:8000/**  
- 自动加载今日 AI 日报，并以 **Markdown 格式** 渲染展示  
- 页面提供：  
  - **刷新（走缓存）**：再次请求 `/daily`，优先用当日缓存  
  - **重新抓取并生成**：请求 `/daily?force_refresh=true`，重新抓 RSS + 去重 + 调用 DeepSeek 生成  
  - **下载 Markdown**：跳转 `/daily.md`，下载今日日报的 `.md` 内容  

### API 端点

| 端点                               | 说明                                                      |
| ---------------------------------- | --------------------------------------------------------- |
| `GET /`                            | 极简网页：展示今日日报、刷新、重新生成、下载 Markdown     |
| `GET /daily`                       | 返回今日日报 JSON（抓取 + 去重 + 生成/缓存）              |
| `GET /daily?force_refresh=true`    | 强制重新抓取并重新生成，忽略当日缓存                      |
| `GET /daily.md`                    | 返回今日日报的 **Markdown 纯文本**，可直接保存为 .md 文件 |
| `GET /daily.md?force_refresh=true` | 同上，但强制重新生成后再返回 Markdown                     |
| `GET /health`                      | 健康检查 `{"status":"ok"}`                                |
| `GET /docs`                        | Swagger API 文档                                          |

### 调用示例

```bash
# 获取今日日报 JSON
curl http://localhost:8000/daily

# 强制重新生成
curl "http://localhost:8000/daily?force_refresh=true"

# 下载 Markdown（浏览器会得到纯文本）
curl -o daily.md http://localhost:8000/daily.md
```

### /daily 返回示例

```json
{
  "success": true,
  "data": {
    "date": "2026-02-10",
    "source": "DeepSeek",
    "titles": ["标题一", "标题二", "标题三"],
    "report": "📌 今日最重要的 3 件事\n...\n⭐ 今日信息价值评分：4 / 5\n- 评分理由：...",
    "from_cache": false,
    "raw_news_count": 42,
    "unique_news_count": 28
  }
}
```

---

## 📡 新闻源配置

RSS 源在 **`fetch_news.py`** 的 `RSS_SOURCES` 中配置，当前为国内科技媒体：

```python
RSS_SOURCES = [
    "https://36kr.com/feed",           # 36氪
    "https://sspai.com/feed",           # 少数派
    "https://www.huxiu.com/rss/0.xml", # 虎嗅
    "https://www.geekpark.net/rss",    # 极客公园
    "https://www.ithome.com/rss/",     # IT之家
]
```

可自行增删或替换为其他 RSS 地址；`fetch_news(limit=30, sources=...)` 支持传入自定义源列表。

---

## 📝 核心模块说明

### fetch_news.py

- **作用**：从 RSS 源抓取新闻  
- **函数**：`fetch_news(limit=30, sources=None) -> list[dict]`  
- **返回字段**：`title`、`summary`、`link`  
- 单源失败不影响其他源，无标题条目会自动过滤  

### deduplicate.py

- **作用**：按标题相似度去重  
- **函数**：`deduplicate_news(news_list, threshold=0.8) -> list[dict]`  
- **说明**：`threshold` 越高去重越严（0–1）  

### generate_daily.py

- **作用**：调用 DeepSeek 生成日报正文与标题，并按日缓存  
- **主入口**：`generate_daily(news_list, force_refresh=False)`  
- **要点**：  
  - 使用 `deepseek-chat`，通过 `DEEPSEEK_API_KEY` 初始化客户端  
  - 同一天内默认读缓存；`force_refresh=True` 时忽略缓存、重新生成  
  - 缓存文件：`data/daily_YYYY-MM-DD.json`  

### prompt.py

- **作用**：定义 `DAILY_PROMPT`，约束日报风格与结构（今日 3 件事、背后逻辑、风险、一句话总结、信息价值评分）  

---

## ⚙️ 可调参数

| 位置                                        | 参数          | 说明                                 |
| ------------------------------------------- | ------------- | ------------------------------------ |
| `fetch_news`                                | `limit`       | 每源最多抓取条数（默认 30）          |
| `deduplicate_news`                          | `threshold`   | 标题相似度阈值（默认 0.8）           |
| `generate_daily_report`                     | `max_news`    | 参与生成日报的新闻条数上限（默认 5） |
| `generate_daily.py`                         | `MODEL`       | 模型名（默认 `deepseek-chat`）       |
| `generate_daily_report` / `generate_titles` | `temperature` | 正文 0.7、标题 0.8，可按需调整       |

---

## 🔧 开发建议

- **API Key**：勿将 `.env` 提交到版本控制；生产环境建议用系统环境变量  
- **日志**：可在 `app.py`、`generate_daily.py` 中增加 `logging` 便于排查网络/API 错误  
- **缓存**：当前按自然日一份；若需多版本可扩展缓存 key（如带时间或版本号）  

