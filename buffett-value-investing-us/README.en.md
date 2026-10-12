# 📈 Buffett-Style Value Investing (US Stocks) | 5-Year Financial Gates + PE/PB Percentile

**[中文](README.md) | [English](README.en.md) | [日本語](README.ja.md)**

Author: Serennity007 (original) | License: MIT | Data: akshare (East Money US financial indicators / Sina US daily bars)

Screen US stocks with Buffett's financial gates and run a deep dive on a single name: five consecutive years of ROE, gross-margin stability, debt-to-assets, positive operating cash flow — plus where today's PE and PB sit inside the stock's own five-year range. The default universe is a NASDAQ-100 list shipped with the repo (101 tickers, with source and fetch date); pass your own codes any time.

## Quick start

```bash
pip install akshare pandas

# Score the bundled universe (101 names, 3 API calls each)
python scripts/screen.py --top 20 --out result.csv

# Score your own list
python scripts/screen.py --tickers MSFT,COST,PEP,ADBE

# Single-name deep dive (includes the manual moat checklist)
python scripts/analyze.py --ticker MSFT
```

## Sample output (measured 2026-10-12, 7-name sample)

```
ticker  total  roe_score  gross_score  debt_score  fcf_score  valuation_score pe_pct pb_pct  data_years
  MSFT     89         30           20           8         20               11   0.37   0.22           5
  ADBE     88         30           20           3         20               15   0.01   0.01           5
  NVDA     83         30           10          15         20                8   0.26      —           5
  COST     70         30           10           3         20                7   0.45   0.40           5
```

```
=== Pulled out of the ranking: metrics unmeasurable (3) ===
ticker  total  gross_score  fcf_score  valuation_score  debt_latest                 flag
  BKNG     48           20         20                8        119.1 权益≤0，ROE/负债率/PB 均不适用
  ORLY     44           20         20                4        104.6 权益≤0，ROE/负债率/PB 均不适用
  SBUX     40           20         20                0        125.3 权益≤0，ROE/负债率/PB 均不适用
```

The `flag` column is the script's own Chinese output: "equity ≤ 0, so ROE, debt ratio and PB are all inapplicable".

Cut lines: **≥80 go to manual moat review; 60–79 have a clear weak leg; <60 does not fit the framework.** Full ranking in [docs/demo.md](docs/demo.md).

## The gates

| Dimension | Standard | Field |
|---|---|---|
| ROE | > 15% in all five years | `ROE_AVG` |
| Gross margin | mean > 30% and five-year spread < 5pp | `GROSS_PROFIT_RATIO` |
| Debt-to-assets | < 50% (not applicable to financials) | `DEBT_ASSET_RATIO` |
| Free cash flow | positive in all five years (OCF + purchases of fixed assets) | both items from the cash-flow statement |
| Valuation | PE / PB low in the stock's own five-year range | built from daily price × fiscal-year EPS / ROE |

Weights in [references/scoring_rules.md](references/scoring_rules.md); the judgment framework for moats and capital allocation in [references/buffett_principles.md](references/buffett_principles.md).

## Three deliberate differences from the A-share version

1. **The universe is a static file.** The A-share build can pull CSI 300 constituents live; the all-US-listings endpoint is unreachable from some networks, so this skill ships `data/universe_nasdaq100.json` with `source` / `as_of` / `fetched_at`. Refresh it yourself as constituents change quarterly, or override with `--tickers`.
2. **The cash-flow gate and the distortion handling were retuned for US data** (free cash flow instead of operating cash flow; negative-equity names marked N/A; cut line raised to 80). Scores are therefore **no longer directly comparable** with the A-share skill — see [references/scoring_rules.md](references/scoring_rules.md).
3. **PE/PB percentiles are approximations.** There is no daily historical valuation endpoint for US listings, so daily PE = close ÷ that fiscal year's basic EPS and daily PB = PE × ROE (P/B = P/E × E/B is an identity). EPS and ROE are held constant within a fiscal year and filing lags are ignored — use the percentile to judge "expensive or cheap versus its own history", nothing more.

## Files

- `SKILL.md` — skill definition for agents
- `scripts/screen.py` — universe scoring (`--universe` / `--tickers` / `--top` / `--out` / `--sleep`)
- `scripts/analyze.py` — single-name report (`--ticker` / `--years` / `--out`)
- `data/universe_nasdaq100.json` — default universe with provenance
- `references/` — scoring rules and principles
- `docs/demo.md` — full measured ranking

## Known data limits

- Some companies have no coverage in the East Money US financial endpoint (the script reports it and continues); insurers are the common case.
- Multi-class or dotted tickers need the exact form: Berkshire is `BRK.B`.
- Fiscal year-ends differ (Microsoft June, NVIDIA January, Apple September) — comparisons are against a company's own history, never across sectors.

## Disclaimer

For study and research only; not investment advice. Financials come from third-party endpoints and may be missing, delayed or restated. Before acting, verify against the primary filings on SEC EDGAR (10-K / 10-Q).
