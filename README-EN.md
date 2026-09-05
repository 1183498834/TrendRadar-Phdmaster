<div align="center" id="trendradar">

# TrendRadar · PhD Position Collector

</div>

> A customized fork of [TrendRadar](https://github.com/sansan0/TrendRadar), focused on collecting **salaried PhD positions in Northern Europe**.

<div align="center">

**[中文](README.md)** | **English**

</div>

## 🙏 Credits

This project is a fork of [TrendRadar](https://github.com/sansan0/TrendRadar) by [sansan0](https://github.com/sansan0). The original author built the complete hot-topic aggregation and notification framework; this fork adds a PhD position crawler on top of it. Many thanks to sansan0 for the excellent work and open-source spirit.

## 🎓 PhD Position Collection (core of this project)

This project adds a PhD position crawler to the original TrendRadar, collecting salaried PhD and Postdoc positions in Northern European countries, and pushing them via Feishu / DingTalk / Telegram / Email and other channels.

### Which data sources are crawled?

Positions come from two sources:

| Source | Description | Dependency |
|--------|-------------|------------|
| [Academic Positions](https://academicpositions.com) | European academic job aggregator | Requires `cloudscraper` to bypass Cloudflare |
| [EURAXESS](https://euraxess.ec.europa.eu) | Official EU job portal | Plain HTTP requests, no bypass needed |

By default it crawls positions in 4 Nordic countries: Norway, Netherlands, Sweden, and Finland.

Crawled positions are classified by title keywords (PhD / Postdoc / Doctoral), deduplicated, and compared incrementally against `data/phd_jobs_snapshot.json` in the repo, so only **new** positions are pushed to avoid repeated notifications. The snapshot is committed back to the repo by GitHub Actions after each run, persisting the incremental baseline across runs.

> The default config is `phd_jobs.push_only: true`, which means **only PhD positions are pushed** — no hot-topic / RSS / AI analysis. Set it to `false` to also push other content.

### How to add my own information sources

#### Option 1: Add a generic RSS feed (recommended, simplest)

Any website that provides an RSS / Atom feed can be added without writing code. Edit `config/config.yaml` and add an entry under `rss.feeds`:

```yaml
rss:
  enabled: true
  feeds:
    - id: "my-feed"                          # unique identifier, any string
      name: "My source"                      # display name
      url: "https://example.com/feed.xml"    # RSS / Atom URL
    # Optional: control freshness filtering for this feed (0 = no filter, push all)
    # max_age_days: 0
```

Save and re-run to take effect.

#### Option 2: Toggle PhD job sources

The two PhD job sources currently only support toggling on/off — adding a third source via config is not supported:

```yaml
phd_jobs:
  sources:
    academicpositions:
      enabled: true    # false = disable Academic Positions
    euraxess:
      enabled: true    # false = disable EURAXESS
```

> To add a new job website, you need to develop a new crawler module (see `academicpositions.py` and `euraxess.py` under `trendradar/crawler/phd_jobs/`) — this is development work, not supported at the config level.

### How to add a country I care about

Adding a target country requires editing **3 places** (all three are required, otherwise the country is silently ignored):

**Place 1: `config/config.yaml`** — add a country entry under `phd_jobs.countries`, providing both source parameters:

```yaml
phd_jobs:
  countries:
    Norway:
      euraxess_id: 768              # EURAXESS country taxonomy ID
      academicpositions_slug: norway
    # ... other existing countries ...
    Denmark:                        # ← new country
      euraxess_id: 757              # see below for how to obtain
      academicpositions_slug: denmark
```

**Place 2: `trendradar/core/loader.py`** — the country whitelist is hardcoded; you must add the new country to the tuple, otherwise it is silently dropped:

```python
"COUNTRIES": [
    c for c in ("Norway", "Netherlands", "Sweden", "Finland", "Denmark") if c in countries
] or list(countries.keys()),
```

**Place 3: `trendradar/crawler/phd_jobs/config.py`** — add the country mapping for both sources:

```python
EURAXXESS_COUNTRY_IDS = {
    "Norway": 768,
    "Netherlands": 798,
    "Sweden": 770,
    "Finland": 760,
    "Denmark": 757,        # ← new
}

ACADEMICPOSITIONS_COUNTRY_SLUGS = {
    "Norway": "norway",
    "Netherlands": "netherlands",
    "Sweden": "sweden",
    "Finland": "finland",
    "Denmark": "denmark",  # ← new
}
```

**(Optional) Place 4: `trendradar/crawler/phd_jobs/adapter.py`** — add the flag emoji for push display:

```python
COUNTRY_FLAGS = {
    "Norway": "🇳🇴 Norway",
    "Netherlands": "🇳🇱 Netherlands",
    "Sweden": "🇸🇪 Sweden",
    "Finland": "🇫🇮 Finland",
    "Denmark": "🇩🇰 Denmark",  # ← new
}
```

#### How to obtain the EURAXESS country ID and Academic Positions slug

- **EURAXESS country ID**: open the [EURAXESS job search](https://euraxess.ec.europa.eu/jobs/search), check a target country in the left filter panel, and look at the `job_country[]` parameter in the address bar — that value is the country's taxonomy ID.
- **Academic Positions slug**: open [Academic Positions](https://academicpositions.com), go to the target country's job page; the URL looks like `https://academicpositions.com/jobs/country/denmark`, where `denmark` is the slug.

Verified EURAXESS country IDs (obtain others with the method above):

| Country | EURAXESS ID |
|---------|-------------|
| Norway | 768 |
| Netherlands | 798 |
| Sweden | 770 |
| Finland | 760 |
| Denmark | 757 |
| Germany | 794 |
| France | 793 |
| Iceland | 762 |

### Which files do I need to modify? Overview

| Purpose | File | Location |
|---------|------|----------|
| Add RSS source | `config/config.yaml` | `rss.feeds` |
| Toggle PhD sources | `config/config.yaml` | `phd_jobs.sources` |
| Add country (place 1) | `config/config.yaml` | `phd_jobs.countries` |
| Add country (place 2, required) | `trendradar/core/loader.py` | country whitelist tuple |
| Add country (place 3, required) | `trendradar/crawler/phd_jobs/config.py` | `EURAXXESS_COUNTRY_IDS` / `ACADEMICPOSITIONS_COUNTRY_SLUGS` |
| Add country (place 4, optional) | `trendradar/crawler/phd_jobs/adapter.py` | `COUNTRY_FLAGS` |
| Notification channels | `config/config.yaml` | `notification.channels` |
| Keyword filtering | `config/frequency_words.txt` | whole file |

---

## 🚀 How to run

Choose one of two ways:

**Option 1: GitHub Actions (already configured, recommended)**

`.github/workflows/crawler.yml` in this repo already configures scheduled crawling (runs daily at UTC 1:00 by default). Just configure the notification channel secrets in repo Settings → Secrets (e.g. `FEISHU_WEBHOOK_URL`, `TELEGRAM_BOT_TOKEN`), and it will run and push automatically.

**Option 2: Run locally**

```bash
uv sync --frozen --no-dev    # install dependencies
uv run python -m trendradar  # run one crawl + push
```

Notification channels are configured in the `notification.channels` section of `config/config.yaml` (Feishu / DingTalk / Telegram / Email, etc.).

## 📄 License

GPL-3.0 License

---

<div align="center">

[🔝 Back to top](#trendradar)

</div>
