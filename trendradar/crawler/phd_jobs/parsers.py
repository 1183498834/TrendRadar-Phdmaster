# coding=utf-8
"""职位数据标准化:类型分类、合并去重、归一化 key。

职位类型识别(基于标题关键词):
  - phd:      标题含 phd / ph.d(不含 postdoc)
  - doctoral: 标题含 doctoral / doctorate(不含 post 前缀变体)
  - postdoc:  标题含 postdoc / post-doc / postdoctoral / post-doctoral
"""

import re
import unicodedata

# 博士后前缀变体
_POSTDOC_PAT = re.compile(r"post[- ]?doctor|post[- ]?doc", re.I)
# 独立 doctoral 词(不跟随 post 前缀)
_DOCTORAL_PAT = re.compile(r"\bdoctor(al|ate)?\b", re.I)
# PhD 变体
_PHD_PAT = re.compile(r"\bph\.?d\b", re.I)


def _normalize(s):
    """标题归一化:小写、去重音、去空白,用于对比匹配。"""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def classify_position(title):
    """按标题判定职位类型,返回 "phd" | "postdoc" | "doctoral" | None。"""
    t = title.lower()
    if _POSTDOC_PAT.search(t):
        return "postdoc"
    if _PHD_PAT.search(t):
        return "phd"
    if _DOCTORAL_PAT.search(t):
        return "doctoral"
    return None


def is_phd_title(title):
    """是否命中博士相关关键词(phd/postdoc/doctoral 之一)。"""
    return classify_position(title) is not None


def job_key(job):
    """生成用于增量对比的唯一 key:优先 url,兜底归一化标题。"""
    if job.get("url"):
        # 去掉页码/跟踪参数,只保留稳定的路径
        url = re.sub(r"[?#].*$", "", job["url"])
        return url
    return _normalize(job.get("title", ""))


def _matches_types(position, position_types):
    """职位类型是否在允许集合内。

    position_types 可为 None/空(不过滤)或 ["phd","postdoc","doctoral"]。
    """
    if not position_types:
        return True
    if not position:
        return True  # 无法识别类型时保留,避免误杀
    return position in position_types


def merge_dedupe(jobs, target_countries, position_types=None):
    """按 job_key 去重,过滤非博士标题、目标国家外的职位,并按类型筛选。"""
    seen = {}
    for job in jobs:
        if not job.get("title"):
            continue
        position = classify_position(job["title"])
        if position is None:
            continue
        if not _matches_types(position, position_types):
            continue
        country = job.get("country")
        if country and target_countries and country not in target_countries:
            continue  # EURAXESS 国家过滤并不严格,按卡片标签兜底剔除
        k = job_key(job)
        if k and k not in seen:
            seen[k] = job
    return list(seen.values())
