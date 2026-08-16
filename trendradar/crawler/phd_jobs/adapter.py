# coding=utf-8
"""职位列表 → 独立展示区数据 的适配器。

把职位映射为 standalone_data["rss_feeds"],每国一个 feed,item 复用
splitter 的 _format_standalone_rss_item 形状:{title, url, published_at, author}。
这样无需改动任何渲染代码,所有推送渠道自动生效。
"""

from .parsers import classify_position

COUNTRY_FLAGS = {
    "Norway": "🇳🇴 Norway",
    "Netherlands": "🇳🇱 Netherlands",
    "Sweden": "🇸🇪 Sweden",
}

POSITION_LABELS = {
    "phd": "PhD",
    "postdoc": "Postdoc",
    "doctoral": "Doctoral",
}


def _item(job):
    """单个职位 → standalone rss item。"""
    title = job.get("title", "")
    employer = job.get("employer") or ""
    if employer and employer.lower() not in title.lower():
        title = f"{title} @ {employer}"

    meta_parts = []
    position = classify_position(job.get("title", ""))
    if position:
        meta_parts.append(POSITION_LABELS.get(position, position))
    city = job.get("city")
    country = job.get("country")
    if city:
        meta_parts.append(city)
    elif country:
        meta_parts.append(country)
    deadline = job.get("deadline")
    if deadline:
        meta_parts.append(f"截止 {deadline}")
    posted = job.get("posted_date")
    if posted and not deadline:
        meta_parts.append(f"发布于 {posted}")

    return {
        "title": title,
        "url": job.get("url", ""),
        "published_at": "",
        "author": " | ".join(meta_parts),
        "source": job.get("source", ""),
        "position": position,
    }


def build_standalone(jobs, countries):
    """职位列表 → standalone_data 形状。

    返回 {"platforms": [], "rss_feeds": [{id, name, items}]},每国一个 feed。
    """
    by_country = {}
    for job in jobs:
        country = job.get("country") or "Other"
        by_country.setdefault(country, []).append(job)

    feeds = []
    for country in countries:
        items = by_country.get(country)
        if not items:
            continue
        label = COUNTRY_FLAGS.get(country, country)
        feeds.append({
            "id": f"phd-{country.lower()}",
            "name": f"{label} PhD 职位",
            "items": [_item(j) for j in items],
        })

    return {"platforms": [], "rss_feeds": feeds}
