import os
import json
import re
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from prompt import DAILY_PROMPT

# =========================
# 基础配置
# =========================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MODEL = "deepseek-chat"


# =========================
# 初始化 DeepSeek Client
# =========================

def get_client() -> OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("❌ 未检测到 DEEPSEEK_API_KEY，请检查 .env 文件中的 DEEPSEEK_API_KEY")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )


def _chat_completion(*, client: OpenAI, prompt: str, temperature: float) -> str:
    """
    封装一次通用的 chat.completions 调用，避免重复代码。
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
    except Exception as e:
        raise RuntimeError(f"❌ DeepSeek 调用失败: {e}")

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("❌ DeepSeek 返回内容为空")

    return content


# =========================
# 缓存工具函数
# =========================

def _cache_path(date_str: str) -> Path:
    return DATA_DIR / f"daily_{date_str}.json"


def load_cache(date_str: str):
    path = _cache_path(date_str)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(date_str: str, data: dict):
    path = _cache_path(date_str)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 生成 AI 日报正文
# =========================

def generate_daily_report(client: OpenAI, news_list, max_news: int = 5) -> str:
    """
    根据新闻列表生成日报正文。
    """
    if not news_list:
        raise RuntimeError("❌ 今日没有可用新闻，无法生成日报")

    news_list = list(news_list)[:max_news]

    news_text = "\n".join(
        f"- {n.get('title', '').strip()}：{n.get('summary', '').strip()}"
        for n in news_list
        if n.get("title")
    )

    if not news_text:
        raise RuntimeError("❌ 新闻列表中缺少有效标题，无法生成日报")

    prompt = DAILY_PROMPT.format(news=news_text)
    return _chat_completion(client=client, prompt=prompt, temperature=0.7)


# =========================
# 生成标题 & 解析为 list
# =========================

def generate_titles(client: OpenAI, daily_report: str) -> list[str]:
    """
    基于日报正文生成 3 个公众号风格标题。
    """

    title_prompt = f"""
你是一位非常擅长写公众号标题的编辑。

请基于下面这份 AI 日报内容，生成 3 个不同风格的标题。

要求：
1. 不要标题党
2. 有信息量
3. 有判断或情绪
4. 每个标题不超过 25 个字
5. 使用中文

输出格式（严格按照下面的格式输出）：
1. 标题一
2. 标题二
3. 标题三

日报内容如下：
{daily_report}
"""

    raw_text = _chat_completion(
        client=client,
        prompt=title_prompt,
        temperature=0.8,
    )

    # 解析成 list（非常关键）
    titles: list[str] = []
    for line in raw_text.splitlines():
        match = re.match(r"^\s*\d+[\.、]\s*(.+)$", line.strip())
        if match:
            titles.append(match.group(1).strip())

    # 容错：如果模型没有完全按格式来，兜个底
    if not titles:
        titles = [raw_text.strip()[:25]] if raw_text.strip() else []

    return titles[:3]


# =========================
# 对外主函数（给 app.py 用）
# =========================

def generate_daily(news_list, *, force_refresh: bool = False):
    """
    主入口：
    - 同一天自动走缓存（除非 force_refresh=True）
    - 返回结构化数据
    """

    today = datetime.now().strftime("%Y-%m-%d")

    # 1️⃣ 先查缓存
    cached = load_cache(today)
    if cached and not force_refresh:
        # 标记来自缓存，方便上层判断
        cached["from_cache"] = True
        return cached

    client = get_client()

    # 2️⃣ 生成日报正文
    daily_report = generate_daily_report(
        client=client,
        news_list=news_list,
    )

    # 3️⃣ 生成标题
    titles = generate_titles(
        client=client,
        daily_report=daily_report,
    )

    result = {
        "date": today,
        "source": "DeepSeek",
        "titles": titles,
        "report": daily_report,
        "from_cache": False,
    }

    # 4️⃣ 写入缓存
    save_cache(today, result)

    return result
