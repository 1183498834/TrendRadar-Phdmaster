# coding=utf-8
"""EURAXESS 爬虫:抓取挪威/荷兰/瑞典的博士职位。

EURAXESS 是欧盟官方职位库,无需绕过防护,普通 requests 即可。
搜索页卡片结构(实测):
  - 卡片:ul.unformatted-list > li > div#job-teaser-content
  - 国家标签:span.ecl-label--highlight
  - 机构:li.ecl-content-block__primary-meta-item 内第一个 a
  - 发布日期:"Posted on: DD Month YYYY"
  - 标题:h3.ecl-content-block__title > a > span
  - 描述:div.ecl-content-block__description
  - 截止日期:卡片内 <time datetime=...>(每卡唯一)
  - 详情链接:/jobs/{id}
"""

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .config import EURAXXESS_COUNTRY_IDS, USER_AGENT

BASE_URL = "https://euraxess.ec.europa.eu"

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}


def _parse_posted(text):
    """把 'Posted on: 15 August 2026' 转成 YYYY-MM-DD。"""
    m = re.match(r"\s*Posted on:\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    if not m:
        return None
    day, mon, year = int(m.group(1)), MONTHS.get(m.group(2).lower()), int(m.group(3))
    if not mon:
        return None
    try:
        return datetime(year, mon, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _parse_deadline(card):
    """提取截止日期:每张职位卡片只有一个 <time>,取其 datetime。"""
    time_tag = card.find("time")
    if time_tag and time_tag.get("datetime"):
        return time_tag["datetime"][:10]
    return None


def _parse_card(card):
    """从单个职位卡片提取字段。失败返回 None。"""
    try:
        # 唯一 ID 与详情链接
        title_a = card.select_one("h3.ecl-content-block__title a")
        if not title_a:
            return None
        href = title_a.get("href", "")
        m = re.search(r"/jobs/(\d+)", href)
        job_id = m.group(1) if m else href
        url = href if href.startswith("http") else BASE_URL + href

        # 标题
        span = title_a.select_one("span")
        title = span.get_text(strip=True) if span else title_a.get_text(strip=True)

        # 机构 + 发布日期:都在 primary-meta-item
        employer = ""
        posted = None
        for item in card.select("li.ecl-content-block__primary-meta-item"):
            a = item.select_one("a")
            if a and not employer:
                employer = a.get_text(strip=True)
            txt = item.get_text(" ", strip=True)
            if "Posted on:" in txt:
                posted = _parse_posted(txt)

        # 国家标签
        country = ""
        label = card.select_one("span.ecl-label--highlight")
        if label:
            country = label.get_text(strip=True)

        # 描述
        desc = ""
        desc_div = card.select_one("div.ecl-content-block__description")
        if desc_div:
            desc = desc_div.get_text(" ", strip=True)

        return {
            "id": job_id,
            "title": title,
            "employer": employer,
            "country": country,
            "city": None,
            "posted_date": posted,
            "deadline": _parse_deadline(card),
            "description": desc,
            "url": url,
            "source": "euraxess",
        }
    except Exception as exc:
        print(f"  [phd] euraxess 卡片解析失败: {exc}")
        return None


def fetch_jobs(countries=None, max_pages=3, request_interval_ms=800):
    """单次请求同时覆盖多国(多 country ID 参数),再分页。"""
    countries = countries or list(EURAXXESS_COUNTRY_IDS.keys())
    results = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    ids = [EURAXXESS_COUNTRY_IDS[c] for c in countries if c in EURAXXESS_COUNTRY_IDS]
    if not ids:
        return results
    country_qs = "&".join(f"job_country%5B%5D={cid}" for cid in ids)

    for page in range(0, max_pages):
        url = (
            f"{BASE_URL}/jobs/search?{country_qs}"
            f"&offer_type=job_offer&keywords=PhD&page={page}"
        )
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code != 200:
                print(f"  [phd] euraxess 第{page + 1}页 HTTP {resp.status_code},跳过")
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("#job-teaser-content")
            if not cards:
                print(f"  [phd] euraxess 第{page + 1}页无职位卡片,结束分页")
                break
            before = len(results)
            for card in cards:
                job = _parse_card(card)
                if job:
                    results.append(job)
            print(f"  [phd] euraxess 第{page + 1}页: +{len(results) - before} 条")
            if len(cards) < 10:
                break
        except Exception as exc:
            print(f"  [phd] euraxess 第{page + 1}页抓取失败: {exc}")
        time.sleep(request_interval_ms / 1000.0)
    return results
