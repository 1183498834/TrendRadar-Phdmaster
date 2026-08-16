# coding=utf-8
"""PhD 职位配置:国家映射、来源开关、抓取参数。

国家映射来自 config.yaml 的 phd_jobs 段,由 loader 注入。此处提供默认值。
"""

# 默认目标国家
TARGET_COUNTRIES = ["Norway", "Netherlands", "Sweden"]

# EURAXESS 国家的 Drupal taxonomy 数字 ID(实测 768=Norway, 770=Sweden, 798=Netherlands)
EURAXXESS_COUNTRY_IDS = {
    "Norway": 768,
    "Netherlands": 798,
    "Sweden": 770,
}

# Academic Positions 的 country slug
ACADEMICPOSITIONS_COUNTRY_SLUGS = {
    "Norway": "norway",
    "Netherlands": "netherlands",
    "Sweden": "sweden",
}

# 每源每国抓取页数(每页约 10 条)
MAX_PAGES = 3

# 请求间隔(毫秒),避免风控
REQUEST_INTERVAL_MS = 800

# 默认 User-Agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
