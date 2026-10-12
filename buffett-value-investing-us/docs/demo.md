# 实测榜单：NASDAQ-100 全池打分（调整后口径）

- 运行时间：2026-10-12
- 命令：`python scripts/screen.py --top 25 --out screen_result.csv`
- 结果：**101 只全部取数成功，0 只失败**；其中 **97 只参与排名，4 只因指标失真单列**
- 新判定线分布（94 只满 5 财年者）：**≥80 → 23 只｜60–79 → 37 只｜<60 → 34 只**

口径已针对美股调整（现金流改用 FCF、负权益记 N/A），与 A 股版 `buffett-value-investing` **不再完全可比**。

## 前 25 名

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

读法：CPRT（集装箱租赁）五项全满是本框架的教科书目标；FAST、ODFL 是「生意合格、价格不合格」（估值项仅 7／3 分）；ADBE、INTU、CMCSA、PDD 同时具备「财务达标 + 价格处于自身五年低位」，正是该框架要找的组合。NFLX 的 FCF 项 16 分＝五年里有一年为负（内容支出），说明新口径确实能捕捉到东西。

## 指标失真，未参与排名（4 只）

```
ticker  total  gross_score  fcf_score  valuation_score  debt_latest                 flag
  BKNG     48           20         20                8        119.1 权益≤0，ROE/负债率/PB 均不适用
  ORLY     44           20         20                4        104.6 权益≤0，ROE/负债率/PB 均不适用
  SBUX     40           20         20                0        125.3 权益≤0，ROE/负债率/PB 均不适用
   MAR     40           20         20                0        113.7 权益≤0，ROE/负债率/PB 均不适用
```

这四家都是长期回购把股东权益买穿的公司（资产负债率 >100% ⇔ 权益 ≤ 0）。它们的 ROE 读数分别是 22,573%、5,863%、负值、237%（五年内峰值）——**这不是"极度优秀"，是分母趋零**。旧口径下 BKNG 靠 ROE 白拿满分、又因负债率被判高杠杆，两头都错。现在整只逐出排名，交人工核查（这类公司往往是净现金结构，需要看的是有息负债与利息保障，不是资产负债率）。

## 末位 8 名

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

低分两群：**无连续盈利记录的新股／高增长标的**（RKLB、NBIS、CRWV、SPCX）与**天然高杠杆低 ROE 的公用事业**（XEL、CEG、EXC）。EXC 的 FCF 项 0 分（五年全为负）是公用事业的资本密集特征，不是经营恶化——本框架对这类行业本就不适用。

## 本轮暴露的真实边界（务必连同榜单一起看）

1. **FCF 改造提升了区分度，但幅度有限**：满分占比从旧口径的 **90% 降到 82%**，标准差 3.4 → 4.6。原因是 NASDAQ-100 里连续五年 FCF 为负的公司本来就少。**结论：现金流这一项在本池仍偏弱，真正起作用的是"逐出负权益"那一步。** 见 `references/scoring_rules.md` 的讨论。
2. **13 只标的因薄权益停用 PB 分位**（ROE 峰值 >100% 但权益为正，属真实盈利，仍参与排名）：NVDA、IDXX、ADP、KLAC、QCOM、AAPL、AMGN、FTNT、MRNA、ALNY、APP、WDC、STX。占排名池 13%——意味着 PB 那 7 分对相当一部分优质公司直接失效。
3. **7 只财年数不足 5 年**：ARM、FER、ALAB、SNDK、HONA、SPCX、CRWV。SNDK 只有 1 个财年（2025 年 2 月从西部数据拆分后才独立 reporting），不可与满年份者并列排序。
4. **4 只没有 PE 分位**：HONA、SPCX、CRWV、RKLB——最新财年基本 EPS 非正，PE 无定义。
5. **GOOG 与 GOOGL 各占一席**（同一公司两类股权），人工核查时合并。
6. **`pe_pct = 1.00`（TER）是真实读数**，不是错误：当前 PE 处于自身五年最高位。

## 复现方式

```bash
pip install akshare pandas
git clone https://github.com/Serennity007/us-stock-quant-skills.git
cd us-stock-quant-skills/buffett-value-investing-us
python scripts/screen.py --top 25 --out screen_result.csv
python scripts/analyze.py --ticker CPRT
```

榜单随行情与财报变化；上表是 2026-10-12 的一次快照，不构成投资建议，也不是推荐清单。
