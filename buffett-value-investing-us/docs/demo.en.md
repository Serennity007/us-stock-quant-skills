# Measured ranking: full NASDAQ-100 screen (adjusted US calibration)

- Run date: 2026-10-12
- Command: `python scripts/screen.py --top 25 --out screen_result.csv`
- Result: **all 101 names fetched, 0 failures**; **97 ranked, 4 pulled out as unmeasurable**
- New cut lines (94 names with a full five fiscal years): **≥80 → 23｜60–79 → 37｜<60 → 34**

The gates were retuned for US data (free cash flow instead of operating cash flow; negative equity marked N/A), so scores are **no longer directly comparable** with the A-share skill `buffett-value-investing`.

## Top 25

```
ticker  total  roe_score  gross_score  debt_score  fcf_score  valuation_score pe_pct pb_pct  data_years
  CPRT    100         30           20          15         20               15    0.01    0.01           5
  REGN     97         27           20          15         20               15    0.24    0.11           5
  FAST     92         30           20          15         20                7    0.50    0.50           5
  ISRG     91         21           20          15         20               15    0.05    0.23           5
   TRI     91         21           20          15         20               15    0.26    0.01           5
  INTU     90         27           20           8         20               15    0.03    0.04           5
  MSFT     89         30           20           8         20               11    0.37    0.22           5
  ADBE     88         30           20           3         20               15    0.01    0.01           5
  ODFL     88         30           20          15         20                3    0.60    0.47           5
  PAYX     85         30           20           0         20               15    0.12    0.13           5
  MPWR     85         30           20          15         20                0    0.97    0.94           5
   PEP     85         30           20           0         20               15    0.11    0.03           5
  ADSK     85         30           20           0         20               15    0.07    0.05           5
   TER     85         30           20          15         20                0    1.00    1.00           5
  GOOG     85         30           20          15         20                0    0.79    0.79           5
 GOOGL     85         30           20          15         20                0    0.79    0.79           5
   PDD     84         24           10          15         20               15    0.00    0.00           5
  NVDA     83         30           10          15         20                8    0.26      —           5
 CMCSA     82         24           20           3         20               15    0.01    0.01           5
  META     81         30           20           8         20                3    0.52    0.45           5
  IDXX     81         30           20           3         20                8    0.13      —           5
  CTAS     80         30           20           3         20                7    0.36    0.37           5
  MNST     80         30           15          15         20                0    0.65    0.71           5
  GEHC     79         24           20           0         20               15    0.04    0.13           5
  NFLX     79         30           15           3         16               15    0.11    0.26           5
```

How to read it: CPRT (container leasing) clearing all five gates is the textbook target. FAST and ODFL are "business passes, price does not" (valuation 7 and 3). ADBE, INTU, CMCSA and PDD combine intact financials with a price in the bottom of their own five-year range — exactly the pairing this framework hunts. NFLX scoring 16 rather than 20 on FCF means one of its five years had negative free cash flow (content spend), so the new gate does catch something.

## Pulled out of the ranking: metrics unmeasurable (4)

```
ticker  total  gross_score  fcf_score  valuation_score  debt_latest                 flag
  BKNG     48           20         20                8        119.1 权益≤0，ROE/负债率/PB 均不适用
  ORLY     44           20         20                4        104.6 权益≤0，ROE/负债率/PB 均不适用
  SBUX     40           20         20                0        125.3 权益≤0，ROE/负债率/PB 均不适用
   MAR     40           20         20                0        113.7 权益≤0，ROE/负债率/PB 均不适用
```

The `flag` column is the script's own output, kept verbatim in Chinese; it reads "equity ≤ 0, so ROE, debt ratio and PB are all inapplicable".

All four are companies whose buybacks have pushed shareholders' equity to or below zero (debt-to-assets above 100% ⇔ equity ≤ 0). Their five-year peak ROE readings are 22,573%, 5,863%, negative, and 237% — **that is not exceptional performance, it is a denominator collapsing toward zero**. Under the old calibration Booking gained full marks for "capital efficiency" and was simultaneously penalised as over-levered: wrong in both directions. They are now removed from the ranking for manual review, where the relevant measures are interest-bearing debt and interest cover, not debt-to-assets.

## Bottom 8

```
ticker  total  roe_score  gross_score  debt_score  fcf_score  valuation_score pe_pct pb_pct  data_years
   XEL     30          0           10           0         20                0    0.87    0.61           5
   CEG     25         15            6           0          4                0    0.64    0.50           5
   EXC     24          0           20           0          0                4    0.47    0.90           5
  SPCX     22          0           15           3          4                0     NaN     NaN           1
  TTWO     21          0           10           3          8                0    0.83    0.83           5
  RKLB     15          0            0          15          0                0     NaN     NaN           5
  NBIS     11          0            0           3          8                0    0.99    0.99           5
  CRWV     10          0           10           0          0                0     NaN     NaN           2
```

Two clusters: **names without a continuous earnings record** (RKLB, NBIS, CRWV, SPCX) and **capital-intensive, structurally levered utilities** (XEL, CEG, EXC). EXC's zero on FCF — negative in all five years — is the capital structure of the regulated utility business, not deteriorating operations; this framework simply does not apply to that sector.

## Real limitations this run exposed (read them with the table)

1. **The FCF change helped, but less than expected**: the share taking full marks fell from **90% to 82%**, standard deviation 3.4 → 4.6. Few NASDAQ-100 members post five consecutive years of negative free cash flow, so the gate stays weak in this universe. **The change that actually mattered was excluding negative-equity names**, not the FCF substitution. See `references/scoring_rules.md`.
2. **13 names have PB suppressed for thin equity** (peak ROE > 100% with positive equity — genuine earnings, still ranked): NVDA, IDXX, ADP, KLAC, QCOM, AAPL, AMGN, FTNT, MRNA, ALNY, APP, WDC, STX. That is 13% of the ranked pool, i.e. 7 of the 100 points are simply unavailable for a large share of good companies.
3. **Seven names have fewer than five fiscal years**: ARM, FER, ALAB, SNDK, HONA, SPCX, CRWV. SNDK has one — it reports separately only since the February 2025 Western Digital spin-off — and must not be ranked alongside full-history names.
4. **Four names have no PE percentile**: HONA, SPCX, CRWV, RKLB — latest fiscal-year basic EPS is not positive.
5. **GOOG and GOOGL each take a row**: two share classes of one company; merge during manual review.
6. **`pe_pct = 1.00` (TER) is a real reading**: today's PE sits at the top of its own five-year range.

## Reproduce

```bash
pip install akshare pandas
git clone https://github.com/Serennity007/us-stock-quant-skills.git
cd us-stock-quant-skills/buffett-value-investing-us
python scripts/screen.py --top 25 --out screen_result.csv
python scripts/analyze.py --ticker CPRT
```

Rankings move with prices and filings; the table above is a single snapshot from 2026-10-12, is not investment advice, and is not a recommendation list.
