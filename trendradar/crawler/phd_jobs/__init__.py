# coding=utf-8
"""PhD 职位爬虫包:抓取挪威/荷兰/瑞典的岗位制博士职位。

数据源:
  - academicpositions.com(需 cloudscraper 绕过 Cloudflare)
  - euraxess.ec.europa.eu(欧盟官方职位库,普通 requests 即可)

对外接口:
  - fetch_phd_jobs(cfg) -> 去重过滤后的职位列表
  - build_standalone(jobs, countries) -> standalone_data 形状
  - snapshot.load_previous / detect_new / save -> 跨运行增量对比
"""

from .fetcher import fetch_phd_jobs
from .adapter import build_standalone
from .parsers import is_phd_title, job_key
from . import snapshot

__all__ = [
    "fetch_phd_jobs",
    "build_standalone",
    "is_phd_title",
    "job_key",
    "snapshot",
]
