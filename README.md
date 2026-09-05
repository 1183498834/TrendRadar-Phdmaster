<div align="center" id="trendradar">

# TrendRadar · PhD 职位收集

</div>

> 基于 [TrendRadar](https://github.com/sansan0/TrendRadar) 的定制版本，专注于收集**北欧岗位制博士（PhD）职位**信息。

<div align="center">

**中文** | **[English](README-EN.md)**

</div>

## 🙏 鸣谢

本项目是 [TrendRadar](https://github.com/sansan0/TrendRadar)（作者 [sansan0](https://github.com/sansan0)）的一个 fork。原作者搭建了完整的热点聚合与推送框架，本 fork 在其之上新增了 PhD 职位抓取模块。感谢 sansan0 的优秀工作与开源精神。

## 🎓 PhD 职位收集（本项目核心）

本项目在原 TrendRadar 基础上新增了 PhD 职位抓取模块，专门收集北欧国家的岗位制博士（PhD）、博士后（Postdoc）职位，并通过飞书 / 钉钉 / Telegram / 邮件等渠道推送。

### 抓取哪些数据源？

职位信息来自两个数据源：

| 数据源 | 说明 | 依赖 |
|--------|------|------|
| [Academic Positions](https://academicpositions.com) | 欧洲学术职位聚合站 | 需 `cloudscraper` 绕过 Cloudflare |
| [EURAXESS](https://euraxess.ec.europa.eu) | 欧盟官方职位库 | 普通 HTTP 请求，无需绕过 |

默认抓取以下 4 个北欧国家的职位：挪威（Norway）、荷兰（Netherlands）、瑞典（Sweden）、芬兰（Finland）。

抓到的职位会按标题关键词自动分类（PhD / Postdoc / Doctoral）、去重，并与仓库内 `data/phd_jobs_snapshot.json` 做增量对比，只推送**新增**职位，避免重复打扰。快照由 GitHub Actions 每次运行后自动提交回仓库，实现跨运行的增量基准持久化。

> 默认配置 `phd_jobs.push_only: true`，即**只推送 PhD 职位**、不推送热榜 / RSS / AI 分析。若想同时推送其他内容，把它改为 `false`。

### 我要增加自己的信息网址

#### 方式一：添加通用 RSS 信息源（推荐，最简单）

任何提供 RSS / Atom 订阅的网站，都可以直接接入，无需写代码。修改 `config/config.yaml`，在 `rss.feeds` 下新增条目：

```yaml
rss:
  enabled: true
  feeds:
    - id: "my-feed"                          # 唯一标识，任意英文字符串
      name: "我的信息源"                      # 显示名称
      url: "https://example.com/feed.xml"    # RSS / Atom 地址
    # 可选：单独控制该源的新鲜度过滤（0 = 不过滤，推送所有文章）
    # max_age_days: 0
```

保存后重新运行即可生效。

#### 方式二：开关 PhD 职位源

PhD 职位的两个数据源目前只支持开关，不支持通过配置文件新增第三个源：

```yaml
phd_jobs:
  sources:
    academicpositions:
      enabled: true    # false = 关闭 Academic Positions
    euraxess:
      enabled: true    # false = 关闭 EURAXESS
```

> 若需要接入新的职位网站，需要开发新的爬虫模块（参考 `trendradar/crawler/phd_jobs/` 下的 `academicpositions.py` 与 `euraxess.py`），属于开发工作，不在配置文件层面支持。

### 我要增加自己关注的国家

新增目标国家需要同时修改 **3 处**（缺一不可，否则国家会被静默忽略）：

**第 1 处：`config/config.yaml`** —— 在 `phd_jobs.countries` 下新增国家条目，需同时提供两个来源对应的参数：

```yaml
phd_jobs:
  countries:
    Norway:
      euraxess_id: 768              # EURAXESS 的国家 taxonomy ID
      academicpositions_slug: norway
    # ... 其他已有国家 ...
    Denmark:                        # ← 新增国家
      euraxess_id: 757              # 获取方式见下方说明
      academicpositions_slug: denmark
```

**第 2 处：`trendradar/core/loader.py`** —— 国家白名单是硬编码的，必须把新国家加入元组，否则会被静默丢弃：

```python
"COUNTRIES": [
    c for c in ("Norway", "Netherlands", "Sweden", "Finland", "Denmark") if c in countries
] or list(countries.keys()),
```

**第 3 处：`trendradar/crawler/phd_jobs/config.py`** —— 补上两个数据源的国家映射：

```python
EURAXXESS_COUNTRY_IDS = {
    "Norway": 768,
    "Netherlands": 798,
    "Sweden": 770,
    "Finland": 760,
    "Denmark": 757,        # ← 新增
}

ACADEMICPOSITIONS_COUNTRY_SLUGS = {
    "Norway": "norway",
    "Netherlands": "netherlands",
    "Sweden": "sweden",
    "Finland": "finland",
    "Denmark": "denmark",  # ← 新增
}
```

**（可选）第 4 处：`trendradar/crawler/phd_jobs/adapter.py`** —— 补充国旗 emoji，用于推送展示：

```python
COUNTRY_FLAGS = {
    "Norway": "🇳🇴 Norway",
    "Netherlands": "🇳🇱 Netherlands",
    "Sweden": "🇸🇪 Sweden",
    "Finland": "🇫🇮 Finland",
    "Denmark": "🇩🇰 Denmark",  # ← 新增
}
```

#### 如何获取 EURAXESS 国家 ID 与 Academic Positions slug

- **EURAXESS 国家 ID**：打开 [EURAXESS 职位搜索](https://euraxess.ec.europa.eu/jobs/search)，在左侧筛选栏勾选目标国家，观察地址栏中 `job_country[]` 参数的值，即为该国的 taxonomy ID。
- **Academic Positions slug**：打开 [Academic Positions](https://academicpositions.com)，进入目标国家的职位页面，URL 形如 `https://academicpositions.com/jobs/country/denmark`，其中 `denmark` 即为 slug。

已实测的 EURAXESS 国家 ID 速查（其余国家按上述方法自行获取）：

| 国家 | EURAXESS ID |
|------|-------------|
| Norway | 768 |
| Netherlands | 798 |
| Sweden | 770 |
| Finland | 760 |
| Denmark | 757 |
| Germany | 794 |
| France | 793 |
| Iceland | 762 |

### 我需要修改哪些文件？总览

| 目的 | 文件 | 位置 |
|------|------|------|
| 添加 RSS 信息网址 | `config/config.yaml` | `rss.feeds` |
| 开关 PhD 职位源 | `config/config.yaml` | `phd_jobs.sources` |
| 添加国家（第 1 处） | `config/config.yaml` | `phd_jobs.countries` |
| 添加国家（第 2 处，必改） | `trendradar/core/loader.py` | 国家白名单元组 |
| 添加国家（第 3 处，必改） | `trendradar/crawler/phd_jobs/config.py` | `EURAXXESS_COUNTRY_IDS` / `ACADEMICPOSITIONS_COUNTRY_SLUGS` |
| 添加国家（第 4 处，可选） | `trendradar/crawler/phd_jobs/adapter.py` | `COUNTRY_FLAGS` |
| 推送渠道 | `config/config.yaml` | `notification.channels` |
| 关键词过滤 | `config/frequency_words.txt` | 全文 |

---

## 🚀 运行方式

两种方式二选一：

**方式一：GitHub Actions（仓库已配置，推荐）**

本仓库的 `.github/workflows/crawler.yml` 已配置定时抓取（默认每天 UTC 1:00 运行）。只需在仓库 Settings → Secrets 里配置推送渠道对应的 Secret（如 `FEISHU_WEBHOOK_URL`、`TELEGRAM_BOT_TOKEN` 等），即可自动运行并推送。

**方式二：本地运行**

```bash
uv sync --frozen --no-dev    # 安装依赖
uv run python -m trendradar  # 运行一次抓取 + 推送
```

推送渠道配置在 `config/config.yaml` 的 `notification.channels` 段（飞书 / 钉钉 / Telegram / 邮件等）。

## 📄 许可证

GPL-3.0 License

---

<div align="center">

[🔝 回到顶部](#trendradar)

</div>
