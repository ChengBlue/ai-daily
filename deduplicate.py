from difflib import SequenceMatcher
from typing import Iterable, List, Dict


def is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    """
    判断两个标题是否相似。

    :param a: 标题 A
    :param b: 标题 B
    :param threshold: 相似度阈值，0~1 之间，越大越严格
    """
    return SequenceMatcher(None, a, b).ratio() >= threshold


def deduplicate_news(
    news_list: Iterable[Dict[str, str]],
    threshold: float = 0.8,
) -> List[Dict[str, str]]:
    """
    根据标题相似度对新闻列表去重。

    - 只要新新闻标题与已有任意一条的相似度 >= threshold，就视为重复并丢弃。

    :param news_list: 原始新闻列表，每条需要至少包含 "title" 字段
    :param threshold: 标题相似度阈值
    """
    unique: List[Dict[str, str]] = []

    for item in news_list:
        title = item.get("title") or ""
        if not title:
            # 没有标题的新闻基本没有价值，直接跳过
            continue

        if any(is_similar(title, u.get("title", ""), threshold=threshold) for u in unique):
            continue

        unique.append(item)

    return unique
