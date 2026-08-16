# coding=utf-8
"""PhD 职位抓取编排:调用两个数据源,合并去重,返回标准职位列表。"""

from . import academicpositions, euraxess
from .parsers import merge_dedupe


def fetch_phd_jobs(cfg):
    """抓取 PhD 职位。

    Args:
        cfg: 配置字典,形如
            {
                "enabled": True,
                "max_pages": 3,
                "request_interval_ms": 800,
                "position_types": ["phd","postdoc","doctoral"],
                "sources": {"academicpositions": {"enabled": True},
                            "euraxess": {"enabled": True}},
                "countries": [...],
            }
        position_types 决定保留哪些职位类型:
          - None/空:不过滤(全部)
          - ["phd"]:仅博士
          - ["phd","postdoc","doctoral"]:全部三种

    Returns:
        去重并按类型过滤后的职位列表
    """
    countries = cfg.get("countries") or cfg.get("COUNTRIES") or ["Norway", "Netherlands", "Sweden"]
    max_pages = int(cfg.get("max_pages") or cfg.get("MAX_PAGES") or 3)
    interval = int(cfg.get("request_interval_ms") or cfg.get("REQUEST_INTERVAL_MS") or 800)
    position_types = cfg.get("position_types") or cfg.get("POSITION_TYPES") or None

    sources = cfg.get("sources", {}) or {}
    use_ap = (sources.get("academicpositions") or {}).get("enabled", True)
    use_eu = (sources.get("euraxess") or {}).get("enabled", True)

    raw = []
    if use_ap:
        print("[phd] 抓取 academicpositions ...")
        try:
            raw += academicpositions.fetch_jobs(
                countries=countries, max_pages=max_pages,
                request_interval_ms=interval,
            )
        except Exception as exc:
            print(f"  [phd] academicpositions 抓取失败: {exc}")

    if use_eu:
        print("[phd] 抓取 euraxess ...")
        try:
            raw += euraxess.fetch_jobs(
                countries=countries, max_pages=max_pages,
                request_interval_ms=interval,
            )
        except Exception as exc:
            print(f"  [phd] euraxess 抓取失败: {exc}")

    jobs = merge_dedupe(raw, countries, position_types=position_types)
    label = "、".join(position_types) if position_types else "全部"
    print(f"[phd] 原始 {len(raw)} 条,去重+过滤[{label}]后 {len(jobs)} 条")
    return jobs
