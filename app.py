from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from deduplicate import deduplicate_news
from fetch_news import fetch_news
from generate_daily import generate_daily

load_dotenv()  # 一定要最先加载 .env


# =========================
# FastAPI App
# =========================

app = FastAPI(
    title="AI Daily",
    description="AI 日报生成服务",
    version="0.1.0",
)


# =========================
# 内部工具函数：构建当日日报结果
# =========================

def _build_daily_result(force_refresh: bool = False) -> dict:
    """
    抓取 + 去重 + 生成日报，并附加统计信息。
    """
    # 1️⃣ 抓取新闻
    raw_news = fetch_news(limit=30)

    # 可选：将原始新闻写入 data/news.json，方便调试
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    news_path = data_dir / "news.json"
    try:
        import json

        with news_path.open("w", encoding="utf-8") as f:
            json.dump(raw_news, f, ensure_ascii=False, indent=2)
    except Exception:
        # 写调试文件失败不影响主流程
        pass

    # 2️⃣ 去重
    news_list = deduplicate_news(raw_news, threshold=0.8)

    if not news_list:
        raise RuntimeError("未从 RSS 源获取到有效新闻，请稍后重试。")

    # 3️⃣ 生成日报（内部自动处理缓存，可通过 force_refresh 控制）
    result = generate_daily(news_list, force_refresh=force_refresh)

    # 增加一些统计信息，方便确认是否真实抓取 + 去重
    result_with_stats = {
        **result,
        "raw_news_count": len(raw_news),
        "unique_news_count": len(news_list),
    }

    return result_with_stats


# =========================
# 首页：极简网页，展示今日 AI 日报
# =========================

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <title>AI Daily - 今日 AI 日报</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
          :root {
            color-scheme: light dark;
            --bg: #0b1020;
            --card-bg: #151a2b;
            --accent: #3b82f6;
            --accent-soft: rgba(59,130,246,0.15);
            --text-main: #e5e7eb;
            --text-muted: #9ca3af;
            --border-subtle: rgba(148,163,184,0.3);
            --code-bg: #111827;
          }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            min-height: 100vh;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
            background: radial-gradient(circle at top, #1f2937 0, #020617 55%, #000 100%);
            color: var(--text-main);
            display: flex;
            align-items: stretch;
            justify-content: center;
            padding: 32px 16px;
          }
          .shell {
            width: 100%;
            max-width: 960px;
          }
          .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
          }
          .title {
            display: flex;
            align-items: baseline;
            gap: 8px;
          }
          .title h1 {
            font-size: 24px;
            font-weight: 650;
            letter-spacing: 0.03em;
          }
          .title span.badge {
            font-size: 12px;
            padding: 2px 7px;
            border-radius: 999px;
            border: 1px solid var(--border-subtle);
            color: var(--text-muted);
          }
          .actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
          }
          button, .ghost-link {
            border-radius: 999px;
            border: 1px solid transparent;
            font-size: 13px;
            padding: 6px 14px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: var(--accent-soft);
            color: var(--text-main);
            border-color: rgba(59,130,246,0.4);
            transition: background 0.15s ease, transform 0.1s ease, border-color 0.15s ease;
          }
          button.secondary {
            background: transparent;
            border-color: var(--border-subtle);
            color: var(--text-muted);
          }
          button:hover, .ghost-link:hover {
            background: rgba(59,130,246,0.25);
            transform: translateY(-0.5px);
          }
          button.secondary:hover {
            background: rgba(148,163,184,0.12);
          }
          .ghost-link {
            text-decoration: none;
            background: transparent;
            border-color: transparent;
            color: var(--text-muted);
            padding-inline: 4px;
          }
          .meta {
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 12px;
          }
          .meta span + span::before {
            content: "·";
            margin: 0 6px;
            color: #4b5563;
          }
          .card {
            border-radius: 18px;
            background: radial-gradient(circle at top left, rgba(59,130,246,0.25) 0, transparent 45%), var(--card-bg);
            border: 1px solid rgba(148,163,184,0.45);
            padding: 18px 18px 20px;
            box-shadow:
              0 18px 40px rgba(15,23,42,0.9),
              0 0 0 1px rgba(15,23,42,0.9);
          }
          .status-line {
            font-size: 12px;
            margin-bottom: 12px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            gap: 8px;
          }
          .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #22c55e;
            box-shadow: 0 0 0 4px rgba(34,197,94,0.25);
            margin-right: 6px;
          }
          .status-text {
            display: inline-flex;
            align-items: center;
          }
          .report {
            border-radius: 12px;
            padding: 14px 14px 12px;
            background: rgba(15,23,42,0.9);
            border: 1px solid rgba(51,65,85,0.9);
            max-height: calc(100vh - 220px);
            overflow: auto;
          }
          .report h1, .report h2, .report h3 {
            margin: 8px 0 6px;
          }
          .report h1 { font-size: 18px; }
          .report h2 { font-size: 15px; }
          .report h3 { font-size: 14px; }
          .report p {
            margin: 4px 0;
            line-height: 1.6;
          }
          .report ul {
            padding-left: 18px;
            margin: 4px 0;
          }
          .report li {
            margin: 2px 0;
          }
          .report code {
            font-size: 12px;
            background: var(--code-bg);
            padding: 2px 5px;
            border-radius: 4px;
          }
          .report pre {
            margin: 6px 0;
            padding: 6px 8px;
            background: var(--code-bg);
            border-radius: 6px;
            overflow: auto;
          }
          .footer-hint {
            margin-top: 10px;
            font-size: 11px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            gap: 8px;
          }
          @media (max-width: 640px) {
            .header {
              flex-direction: column;
              align-items: flex-start;
              gap: 8px;
            }
            .report {
              max-height: calc(100vh - 230px);
            }
          }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
      </head>
      <body>
        <div class="shell">
          <header class="header">
            <div class="title">
              <h1>📰 AI Daily</h1>
              <span class="badge">今日 AI 日报</span>
            </div>
            <div class="actions">
              <button id="refresh-btn" class="secondary">
                <span>🔄 刷新（走缓存）</span>
              </button>
              <button id="force-btn">
                <span>✨ 重新抓取并生成</span>
              </button>
              <button id="download-btn" class="secondary">
                <span>⬇ 下载 Markdown</span>
              </button>
            </div>
          </header>

          <div id="meta" class="meta"></div>

          <main class="card">
            <div class="status-line">
              <div class="status-text">
                <span class="status-dot" id="status-dot"></span>
                <span id="status-text">正在加载今日 AI 日报…</span>
              </div>
              <div id="stats-text"></div>
            </div>
            <section id="report" class="report">
              <p style="color:#6b7280;font-size:13px;">正在加载内容…</p>
            </section>
            <div class="footer-hint">
              <span>提示：点击「重新抓取并生成」会重新调 DeepSeek 生成今日内容。</span>
              <a class="ghost-link" href="/docs" target="_blank" rel="noreferrer">
                查看 API 文档 ↗
              </a>
            </div>
          </main>
        </div>

        <script>
          async function loadDaily(forceRefresh) {
            const statusText = document.getElementById("status-text");
            const statusDot = document.getElementById("status-dot");
            const statsText = document.getElementById("stats-text");
            const reportEl = document.getElementById("report");
            const metaEl = document.getElementById("meta");

            statusDot.style.background = "#22c55e";
            statusText.textContent = forceRefresh
              ? "正在重新抓取 RSS 并调用 DeepSeek 生成今日日报…"
              : "正在加载今日 AI 日报（可能命中缓存）…";

            try {
              const url = forceRefresh ? "/daily?force_refresh=true" : "/daily";
              const res = await fetch(url);
              const json = await res.json();

              if (!json.success) {
                statusDot.style.background = "#f97316";
                statusDot.style.boxShadow = "0 0 0 4px rgba(248,113,113,0.25)";
                statusText.textContent = "加载失败：" + (json.error || "未知错误");
                reportEl.innerHTML = "<p style='color:#f97316;font-size:13px;'>"
                  + (json.error || "请求失败，请稍后重试。")
                  + "</p>";
                statsText.textContent = "";
                metaEl.textContent = "";
                return;
              }

              const data = json.data || {};
              const date = data.date || "";
              const fromCache = data.from_cache ? "是" : "否";
              const rawCount = data.raw_news_count ?? "–";
              const uniqueCount = data.unique_news_count ?? "–";

              statusDot.style.background = "#22c55e";
              statusDot.style.boxShadow = "0 0 0 4px rgba(34,197,94,0.25)";
              statusText.textContent = "已加载今日 AI 日报";
              statsText.textContent = `抓取 ${rawCount} 条，去重后 ${uniqueCount} 条`;

              metaEl.innerHTML = [
                date ? `日期：${date}` : "",
                `来自缓存：${fromCache}`,
                "来源模型：DeepSeek"
              ].filter(Boolean).join(" ");

              const reportMd = data.report || "暂无内容";
              try {
                if (window.marked) {
                  reportEl.innerHTML = window.marked.parse(reportMd);
                } else {
                  reportEl.textContent = reportMd;
                }
              } catch (e) {
                reportEl.textContent = reportMd;
              }
            } catch (err) {
              statusDot.style.background = "#f97316";
              statusDot.style.boxShadow = "0 0 0 4px rgba(248,113,113,0.25)";
              statusText.textContent = "请求失败，请检查后端服务是否启动。";
              reportEl.innerHTML = "<p style='color:#f97316;font-size:13px;'>"
                + "无法连接到 /daily 接口，请确认 uvicorn 是否正在运行。"
                + "</p>";
              statsText.textContent = "";
              metaEl.textContent = "";
            }
          }

          function setupEvents() {
            const refreshBtn = document.getElementById("refresh-btn");
            const forceBtn = document.getElementById("force-btn");
            const downloadBtn = document.getElementById("download-btn");

            refreshBtn.addEventListener("click", () => loadDaily(false));
            forceBtn.addEventListener("click", () => loadDaily(true));
            downloadBtn.addEventListener("click", () => {
              window.location.href = "/daily.md";
            });
          }

          document.addEventListener("DOMContentLoaded", () => {
            setupEvents();
            loadDaily(false);
          });
        </script>
      </body>
    </html>
    """


# =========================
# 核心接口：生成 AI 日报（真实抓取 + 去重）
# =========================

@app.get("/daily")
def get_daily(force_refresh: bool = False):
    """
    生成今日日报：JSON 版本
    - 正常使用：GET /daily
    - 强制重新生成：GET /daily?force_refresh=true
    """
    try:
        result_with_stats = _build_daily_result(force_refresh=force_refresh)
        return {
            "success": True,
            "data": result_with_stats,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
            },
        )


# =========================
# 下载今日 AI 日报（Markdown）
# =========================

@app.get("/daily.md", response_class=PlainTextResponse)
def get_daily_markdown(force_refresh: bool = False):
    """
    以 Markdown 文本形式返回今日 AI 日报，适合下载或粘贴到笔记工具中。

    - 正常使用：GET /daily.md
    - 强制重新生成：GET /daily.md?force_refresh=true
    """
    try:
        data = _build_daily_result(force_refresh=force_refresh)
        date = data.get("date", "")
        titles = data.get("titles") or []
        report = data.get("report") or ""

        lines = []
        if date:
            lines.append(f"# AI Daily - {date}")
        else:
            lines.append("# AI Daily")
        lines.append("")

        if titles:
            lines.append("## 候选标题")
            for idx, t in enumerate(titles, start=1):
                lines.append(f"{idx}. {t}")
            lines.append("")

        lines.append("## 日报正文")
        lines.append("")
        lines.append(report)
        lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return PlainTextResponse(
            f"生成 Markdown 失败: {e}",
            status_code=500,
        )


# =========================
# 调试接口（可选）
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}
