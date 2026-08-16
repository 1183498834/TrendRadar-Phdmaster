# coding=utf-8
"""Academic Positions 爬虫:抓取挪威/荷兰/瑞典的 PhD 职位列表。

站点使用 Cloudflare 防护,裸 requests 会返回 403,因此依赖 cloudscraper。
职位卡片结构(实测):
  - 卡片:div.list-group-item
  - 雇主:a.job-link(employer 链接)
  - 标题:<a class="...hover-title-underline...job-link"> 内 <h4>
  - 描述:同标题链接内 <p class="text-muted">
  - 城市:div.job-locations 内第一个 <a class="text-muted">
  - 发布时间:Published N days ago / N hours ago
  - 唯一ID:wire:key="job-feedback-{id}-..."
"""

import re
import time
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

import cloudscraper

from .config import ACADEMICPOSITIONS_COUNTRY_SLUGS, USER_AGENT

BASE_URL = "https://academicpositions.com"


def _session():
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    scraper.headers.update({"User-Agent": USER_AGENT})
    return scraper


def _parse_relative_date(text):
    """把 'Published 2 days ago' / '1 month ago' / '3 weeks ago' 转成绝对日期。"""
    m = re.search(r"(\d+)\s+(minute|hour|day|week|month)s?\s+ago", text, re.I)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    now = datetime.now()
    if unit == "minute":
        d = now - timedelta(minutes=n)
    elif unit == "hour":
        d = now - timedelta(hours=n)
    elif unit == "week":
        d = now - timedelta(weeks=n)
    elif unit == "month":
        d = now - timedelta(days=30 * n)
    else:
        d = now - timedelta(days=n)
    return d.strftime("%Y-%m-%d")


def _parse_card(card, country):
    """从单个职位卡片提取字段。失败返回 None。"""
    try:
        # 唯一 ID:优先从 favorite/job-feedback 的 wire:key 提取
        key_m = re.search(r"wire:key=\"(?:job-feedback|favorite)-(\d+)-\d+\"", str(card))
        job_id = key_m.group(1) if key_m else None

        # 标题 + 详情链接 + 描述:都在标题锚点内
        title_a = card.select_one('a[class*="hover-title-underline"]') or card.select_one(
            "a.job-link[href*='/ad/']"
        )
        title = ""
        url = ""
        desc = ""
        if title_a:
            url = title_a.get("href", "")
            h4 = title_a.select_one("h4")
            if h4:
                title = h4.get_text(strip=True)
            p = title_a.select_one("p.text-muted")
            if p:
                desc = p.get_text(strip=True)

        # 雇主
        employer_a = card.select_one('a[href*="/employer/"]')
        employer = employer_a.get_text(strip=True) if employer_a else ""

        # 城市:job-locations 内第一个链接文本
        city = ""
        loc = card.select_one(".job-locations a.text-muted")
        if loc:
            city = loc.get_text(strip=True).rstrip(", ")

        # 发布时间
        posted = None
        m = re.search(r"Published\s+(.+?)\s*</", str(card), re.I)
        if m:
            posted = _parse_relative_date(m.group(1))

        if not title and not url:
            return None

        # 国家按遍历到的 country 参数补充;若卡片内有 country 链接则以卡片为准
        ctry_a = card.select_one('a[href^="/jobs/country/"][class*="text-muted"]')
        if ctry_a and ctry_a.get("href", "").count("/jobs/country/") == 1:
            ctry_slug = ctry_a["href"].rsplit("/", 1)[-1]
            for cn, slug in ACADEMICPOSITIONS_COUNTRY_SLUGS.items():
                if ctry_slug == slug:
                    country = cn
                    break

        return {
            "id": job_id or url.rsplit("/", 1)[-1],
            "title": title,
            "employer": employer,
            "country": country,
            "city": city,
            "posted_date": posted,
            "deadline": None,  # 列表页不含截止日期,详情页才有
            "description": desc,
            "url": url if url.startswith("http") else BASE_URL + url,
            "source": "academicpositions",
        }
    except Exception as exc:
        print(f"  [phd] academicpositions 卡片解析失败: {exc}")
        return None


def fetch_jobs(countries=None, max_pages=3, request_interval_ms=800):
    """遍历国家 × 分页,返回职位列表。单点失败仅告警不中断。"""
    countries = countries or list(ACADEMICPOSITIONS_COUNTRY_SLUGS.keys())
    results = []
    session = _session()
    for country in countries:
        slug = ACADEMICPOSITIONS_COUNTRY_SLUGS.get(country, country.lower())
        for page in range(1, max_pages + 1):
            url = (
                f"{BASE_URL}/jobs/country/{slug}"
                f"?positions=phd&sort=recent&page={page}"
            )
            try:
                resp = session.get(url, timeout=30)
                if resp.status_code != 200:
                    print(
                        f"  [phd] academicpositions {country} 第{page}页 "
                        f"HTTP {resp.status_code},跳过"
                    )
                    continue
                soup = BeautifulSoup(resp.text, "lxml")
                cards = soup.select("div.list-group-item")
                if not cards:
                    print(
                        f"  [phd] academicpositions {country} 第{page}页无职位卡片,结束分页"
                    )
                    break
                before = len(results)
                for card in cards:
                    job = _parse_card(card, country)
                    if job:
                        results.append(job)
                print(
                    f"  [phd] academicpositions/{country} 第{page}页: "
                    f"+{len(results) - before} 条"
                )
                if len(cards) < 10:  # 不足一页则无后续
                    break
            except Exception as exc:
                print(
                    f"  [phd] academicpositions {country} 第{page}页抓取失败: {exc}"
                )
            time.sleep(request_interval_ms / 1000.0)
    return results
