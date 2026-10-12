# Measured ranking: full NASDAQ-100 screen

- Run date: 2026-10-11
- Command: `python scripts/screen.py --top 25 --out screen_result.csv`
- Result: **all 101 names scored, 0 failures** (every call retries with exponential backoff; a couple of codes were transiently rate-limited in an earlier pass and recovered on re-run)
- Distribution: ≥70 → **46**｜50–69 → **33**｜<50 → **22**

## Top 25

```
ticker  total  roe_score  gross_score  debt_score  cashflow_score  valuation_score pe_pct pb_pct  data_years
  CPRT    100         30           20          15              20               15    0.01    0.01           5
  REGN     97         27           20          15              20               15    0.24    0.11           5
  FAST     92         30           20          15              20                7    0.50    0.50           5
  ISRG     91         21           20          15              20               15    0.05    0.23           5
   TRI     91         21           20          15              20               15    0.26    0.01           5
  INTU     90         27           20           8              20               15    0.03    0.04           5
  MSFT     89         30           20           8              20               11    0.37    0.22           5
  IDXX     88         30           20           3              20               15    0.13    0.20           5
  ODFL     88         30           20          15              20                3    0.60    0.47           5
  ADBE     88         30           20           3              20               15    0.01    0.01           5
  NVDA     86         30           10          15              20               11    0.26    0.35           5
  ADSK     85         30           20           0              20               15    0.07    0.05           5
  PAYX     85         30           20           0              20               15    0.12    0.13           5
   TER     85         30           20          15              20                0    1.00    1.00           5
  GOOG     85         30           20          15              20                0    0.79    0.79           5
 GOOGL     85         30           20          15              20                0    0.79    0.79           5
  MPWR     85         30           20          15              20                0    0.97    0.94           5
   ADP     85         30           20           0              20               15    0.16    0.16           5
   PEP     85         30           20           0              20               15    0.11    0.03           5
   PDD     84         24           10          15              20               15    0.00    0.00           5
  NFLX     83         30           15           3              20               15    0.11    0.26           5
 CMCSA     82         24           20           3              20               15    0.01    0.01           5
  META     81         30           20           8              20                3    0.52    0.45           5
  KLAC     80         30           20           3              20                7    0.47    0.45           5
  CTAS     80         30           20           3              20                7    0.36    0.37           5
```

How to read it: businesses that clear all five gates on the strength of switching costs (CPRT, container leasing) are the textbook target of this framework; FAST and ODFL are "quality passes, price does not"; ADBE, INTU and CMCSA combine a ≤0.05 valuation percentile with intact ROE and gross margins, which is exactly the pairing the method hunts for.

## Bottom 8

```
ticker  total  roe_score  gross_score  debt_score  cashflow_score  valuation_score pe_pct pb_pct  data_years
  HONA     37          6           16           3              12                0     NaN     NaN           1
  SPCX     30          0           15           3              12                0     NaN     NaN           1
   XEL     30          0           10           0              20                0    0.87    0.61           5
  CRWV     26          0           10           0              16                0     NaN     NaN           2
  TTWO     25          0           10           3              12                0    0.83    0.83           5
   CEG     25         15            6           0               4                0    0.64    0.50           5
   NBIS     23          0            0           3              20                0    0.99    0.99           5
   RKLB     15          0            0          15               0                0     NaN     NaN           5
```

The bottom clusters into two groups: **recently listed or high-growth names without a continuous earnings record** (RKLB, NBIS, CRWV, ARM, ALAB, SNDK) and **structurally leveraged, low-ROE sectors such as utilities** (XEL, CEG). Neither is a target of this framework — they are "does not fit", not "unjustly punished".

## Real limitations this run exposed (read them with the table)

1. **Seven names have fewer than five fiscal years**: ARM, FER, ALAB, SNDK, HONA, SPCX, CRWV. SNDK has only one — it began reporting separately after the February 2025 Western Digital spin-off — so its ceiling is depressed and it must not be ranked alongside full-history names. The script lists these at the end of every run.
2. **Four names have no PE percentile**: HONA, SPCX, CRWV, RKLB — latest fiscal-year basic EPS is not positive, so PE is undefined.
3. **Five names have no PB percentile**: those four plus **SBUX**. Starbucks is a structural blind spot of this algorithm: years of buybacks leave shareholders' equity at or below zero, so ROE is negative or meaningless, and since this skill derives PB from the identity `PB = PE × ROE`, the identity fails when equity is negative. **For companies whose main capital-allocation tool is buybacks, go back to the balance sheet — do not use this percentile.**
4. **GOOG and GOOGL each take a row**: two share classes of one company, so the ranking double-counts; merge them during manual review.
5. **`pe_pct = 1.00` (TER) is a real reading**, not an error: today's PE sits at the top of its own five-year range.

## Reproduce

```bash
pip install akshare pandas
git clone https://github.com/Serennity007/us-stock-quant-skills.git
cd us-stock-quant-skills/buffett-value-investing-us
python scripts/screen.py --top 25 --out screen_result.csv
python scripts/analyze.py --ticker CPRT
```

Rankings move with prices and filings; the table above is a single snapshot from 2026-10-11 and is not investment advice.
