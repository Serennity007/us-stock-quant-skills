# 实测榜单：NASDAQ-100 全池打分

- 运行时间：2026-10-11
- 命令：`python scripts/screen.py --top 25 --out screen_result.csv`
- 结果：**101 只全部取数成功，0 只失败**（每次调用带指数退避重试；上一轮个别代码偶发限流，重跑即恢复）
- 分布：≥70 分 **46 只**｜50–69 分 **33 只**｜<50 分 **22 只**

## 前 25 名

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

榜单读法：CPRT（集装箱租赁，转换成本型生意）五项全满是这套框架的教科书目标；FAST／ODFL 是「生意合格但当下不便宜」；ADBE、INTU、CMCSA 的估值分位 ≤0.05 说明价格处于自身五年低位，而 ROE／毛利率仍达标——这正是该框架要找的组合。

## 末位 8 名

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

低分集中在两类：**尚未形成连续盈利记录的新上市／高增长标的**（RKLB、NBIS、CRWV、ARM、ALAB、SNDK），以及**公用事业等天然高杠杆、低 ROE 的行业**（XEL、CEG）。这两类都不是本框架的目标，属于「不符合」而非「被错杀」。

## 本轮暴露的真实边界（务必连同榜单一起看）

1. **7 只财年数不足 5 年**：ARM、FER、ALAB、SNDK、HONA、SPCX、CRWV。其中 SNDK 只有 1 个财年（2025-02 从西部数据拆分后才独立 reporting），分数上限被压低，不可与满 5 年者并列比较。脚本会在结尾单独列出这些标的。
2. **4 只没有 PE 分位**：HONA、SPCX、CRWV、RKLB——最新财年基本 EPS ≤ 0，PE 无定义。
3. **5 只没有 PB 分位**：上述 4 只再加 **SBUX**。星巴克是这套算法的结构性盲区：长期回购使股东权益接近或低于零，ROE 因此为负或无意义，而本技能的 PB 是用 `PE × ROE` 恒等式构造的，权益为负时该式失效。**结论：对以回购为资本配置主手段的公司，必须回到资产负债表原值，不能用本分位。**
4. **GOOG 与 GOOGL 各占一席**：同一家公司的两类股权，榜单会重复计入，人工核查时合并处理。
5. **`pe_pct = 1.00`（TER）是真实读数**，不是错误：表示当前 PE 处于自身五年最高位。

## 复现方式

```bash
pip install akshare pandas
git clone https://github.com/Serennity007/us-stock-quant-skills.git
cd us-stock-quant-skills/buffett-value-investing-us
python scripts/screen.py --top 25 --out screen_result.csv
python scripts/analyze.py --ticker CPRT
```

榜单会随行情与财报变化；上表是 2026-10-11 的一次快照，不构成投资建议。
