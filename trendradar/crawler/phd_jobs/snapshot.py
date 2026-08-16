# coding=utf-8
"""PhD 职位快照:跨运行增量对比的基准。

GitHub Actions 每次运行是全新 checkout,SQLite 本地存储不跨运行保留,
因此用仓库内 JSON 文件保存历史 job_key 集,运行后由 workflow 提交回仓库。
"""

import json
import os
from datetime import date

from .parsers import job_key


def _path(cfg):
    return cfg.get("snapshot", {}).get("path") or "data/phd_jobs_snapshot.json"


def load_previous(cfg):
    """读取上次快照的职位 key 集合,无历史返回空 set。"""
    p = _path(cfg)
    if not os.path.exists(p):
        return set()
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        keys = set()
        for job in data.get("jobs", []):
            k = job_key(job)
            if k:
                keys.add(k)
        return keys
    except Exception as exc:
        print(f"  [phd] 快照读取失败({exc}),按首次运行处理")
        return set()


def detect_new(jobs, previous_keys):
    """返回本次职位中,上次未出现(新增)的职位列表。"""
    return [j for j in jobs if job_key(j) and job_key(j) not in previous_keys]


def save(jobs, cfg):
    """写入快照,返回文件路径。"""
    p = _path(cfg)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    data = {
        "crawled_at": date.today().isoformat(),
        "count": len(jobs),
        "jobs": jobs,
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return p
