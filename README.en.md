# us-stock-quant-skills

**[中文](README.md) | [English](README.en.md) | [日本語](README.ja.md)**

![License](https://img.shields.io/badge/License-MIT-blue)
![Data](https://img.shields.io/badge/data-akshare-lightgrey)

A collection of US-stock quant / stock-picking AI skills: reproducible screening and scoring live in scripts, judgment frameworks live in documents, and everything loads as a Claude Code or generic agent skill. All data comes from public endpoints — no API keys.

- **Disclaimer**: study and research only, not investment advice. Conclusions rest on third-party public data that may be missing, delayed or restated; verify against the primary 10-K / 10-Q filings on SEC EDGAR before acting.
- **Started**: 2026-10-11.

## Install a skill

Copy the skill directory you need into your skills folder:

```bash
# Claude Code
cp -r buffett-value-investing-us ~/.claude/skills/

# or a shared agents skills directory
cp -r buffett-value-investing-us ~/.agents/skills/
```

Requirements: `pip install akshare pandas` (Python ≥ 3.9, no API key).

## Skills

| Skill | What it does | Data source |
|---|---|---|
| [buffett-value-investing-us](buffett-value-investing-us) | Buffett-style value investing: five-year ROE / gross-margin / debt / operating-cash-flow gates plus PE and PB percentile against the stock's own history; universe scoring and single-name deep dive | akshare (East Money US financials and cash-flow statements; Sina US daily bars) |

Every skill follows the same layout:

```
<skill>/
├── SKILL.md              # skill definition (agent entry point)
├── README.md/.en/.ja     # trilingual docs
├── scripts/              # runnable scripts
├── references/           # scoring rules + judgment framework
├── data/                 # static data with source and fetch date
└── docs/demo.md          # measured output
```

## Data and provenance

- **Market and financial data**: public endpoints behind [akshare](https://github.com/akfamily/akshare) (East Money, Sina Finance). Every call retries with exponential backoff; one failed name never aborts the run, and failures are summarised at the end.
- **Universe**: `buffett-value-investing-us/data/universe_nasdaq100.json`, taken from Nasdaq's own endpoint `api.nasdaq.com/api/quote/list-type/nasdaq100`, constituents as of **2026-10-09**, fetched **2026-10-11**. Constituents change quarterly and this repository does not auto-sync; use `--tickers` to override.
- **Known endpoint gaps**: unlike the A-share build, US listings have no "all-constituents" or "daily historical valuation" endpoint. The universe is therefore a static file, and PE/PB percentiles are reconstructed from daily prices and fiscal-year EPS/ROE — an approximation, documented in each skill.

## Roadmap

One flagship skill for now, while the data layer and scoring conventions are settled. More US skills follow the same template: momentum / relative strength (CANSLIM), market-cycle thermometer, macro dashboard. All names carry the `-us` suffix so they never collide with the A-share skills in a shared skills directory.

## License

[MIT](LICENSE), © 2026 Serennity007. akshare and its upstream data providers remain under their own terms.
