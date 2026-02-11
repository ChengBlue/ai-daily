from typing import List, Dict, Iterable

import feedparser

RSS_SOURCES: List[str] = [
    # 国内科技媒体 RSS 源
    "https://36kr.com/feed",           # 36氪
    "https://sspai.com/feed",          # 少数派
    "https://www.huxiu.com/rss/0.xml", # 虎嗅
    "https://www.geekpark.net/rss",    # 极客公园
    "https://www.ithome.com/rss/",     # IT之家
]


def _parse_entry(entry) -> Dict[str, str]:
    """
    将 feedparser 的 entry 安全地转换为 dict。
    """
    title = getattr(entry, "title", "") or ""
    summary = getattr(entry, "summary", "") or ""
    link = getattr(entry, "link", "") or ""

    return {
        "title": title.strip(),
        "summary": summary.strip(),
        "link": link.strip(),
    }


def fetch_news(
    limit: int = 30,
    sources: Iterable[str] | None = None,
) -> List[Dict[str, str]]:
    """
    从多个 RSS 源抓取新闻。

    :param limit: 每个源最多抓取多少条
    :param sources: 可选，自定义 RSS 源列表；不传则使用默认 RSS_SOURCES
    """
    news: List[Dict[str, str]] = []
    sources_list = list(sources) if sources is not None else RSS_SOURCES

    for url in sources_list:
        try:
            feed = feedparser.parse(url)
        except Exception:
            # 某个源解析失败时跳过，不影响其他源
            continue

        entries = getattr(feed, "entries", []) or []
        for entry in entries[:limit]:
            item = _parse_entry(entry)
            # 没有标题的新闻意义不大，直接过滤
            if not item["title"]:
                continue
            news.append(item)

    return news
