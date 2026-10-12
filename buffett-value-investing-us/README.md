# 📈 巴菲特式价值投资（美股）｜5年财务门槛 + PE/PB 分位一屏筛完

**[中文](README.md) | [English](README.en.md) | [日本語](README.ja.md)**

作者：Serennity007（原创）| License：MIT | 数据：akshare（东方财富美股财务指标 / 新浪美股日线）

用巴菲特的财务门槛在美股做筛选与单票分析：连续 5 年 ROE、毛利率稳定性、资产负债率、经营现金流为正，再加 PE/PB 相对自身五年的分位。默认股票池是随仓库附带的 NASDAQ-100 清单（101 只，带来源与抓取日期），也可以直接传自选代码。

## 快速开始

```bash
pip install akshare pandas

# 默认股票池打分（101 只，每只 3 次接口调用）
python scripts/screen.py --top 20 --out result.csv

# 只跑自选清单
python scripts/screen.py --tickers MSFT,COST,PEP,ADBE

# 单票深度分析（含护城河人工清单）
python scripts/analyze.py --ticker MSFT
```

## 输出示例（2026-10-12 实测，7 只抽样）

```
ticker  total  roe_score  gross_score  debt_score  fcf_score  valuation_score pe_pct pb_pct  data_years
  MSFT     89         30           20           8         20               11   0.37   0.22           5
  ADBE     88         30           20           3         20               15   0.01   0.01           5
  NVDA     83         30           10          15         20                8   0.26      —           5
  COST     70         30           10           3         20                7   0.45   0.40           5
```

```
=== 指标失真，未参与排名（3 只）===
ticker  total  gross_score  fcf_score  valuation_score  debt_latest                 flag
  BKNG     48           20         20                8        119.1 权益≤0，ROE/负债率/PB 均不适用
  ORLY     44           20         20                4        104.6 权益≤0，ROE/负债率/PB 均不适用
  SBUX     40           20         20                0        125.3 权益≤0，ROE/负债率/PB 均不适用
```

判定线：**≥80 进入人工护城河核查；60–79 有明确短板；<60 不符合本框架**。完整榜单见 [docs/demo.md](docs/demo.md)。

## 筛选标准

| 维度 | 标准 | 数据字段 |
|---|---|---|
| ROE | 连续 5 年 > 15% | `ROE_AVG` |
| 毛利率 | 均值 > 30% 且五年极差 < 5pp | `GROSS_PROFIT_RATIO` |
| 资产负债率 | < 50%（金融股不适用） | `DEBT_ASSET_RATIO` |
| 自由现金流 | 连续 5 年为正（FCF = 经营现金流净额 + 购买固定资产） | 现金流量表两项同取 |
| 估值 | PE / PB 处于自身五年低位 | 日线价 × 财年 EPS / ROE 自行构造 |

权重与判定线见 [references/scoring_rules.md](references/scoring_rules.md)；护城河与资本配置的人工判断框架见 [references/buffett_principles.md](references/buffett_principles.md)。

## 失真处理（美股特有）

回购把股东权益买薄甚至买成负数时，ROE 与 PB 会同时失真（实测 BKNG 的 ROE 峰值 22,573%、ORLY 5,863%）。脚本用「资产负债率 ≥ 100% ⇔ 权益 ≤ 0」判定，命中后 **ROE 与负债率记 N/A、PB 分位置空，整只逐出主榜单单列人工判断**，既不白送分也不误罚。权益为正但 ROE > 100%（如 NVDA）属真实盈利，仍参与排名，只是停用 PB 分位。

## 与 A 股版的三处关键差异

1. **股票池是静态清单**：A 股版可实时拉沪深300 成分股，美股的全市场接口在部分网络环境不可达，因此改为随仓库附带 `data/universe_nasdaq100.json`（含 `source` / `as_of` / `fetched_at`），成分股季度调整需自行更新，或用 `--tickers` 覆盖。
2. **现金流与失真口径按美股重定**：改用 FCF、负权益记 N/A，判定线抬到 80。因此**分数与 A 股版不再直接可比**，详见 [references/scoring_rules.md](references/scoring_rules.md)。
3. **PE/PB 分位是近似值**：美股没有逐日历史估值接口。日 PE = 收盘价 ÷ 当年基本 EPS，日 PB = 日 PE × 当年 ROE（P/B = P/E × E/B 恒等）。假定财年内 EPS/ROE 不变、不含财报发布滞后，只用于判断「相对自身历史贵还是便宜」。

## 配套文件

- `SKILL.md` — 技能定义（供 Agent 加载）
- `scripts/screen.py` — 股票池打分（`--universe` / `--tickers` / `--top` / `--out` / `--sleep`）
- `scripts/analyze.py` — 单票深度分析（`--ticker` / `--years` / `--out`）
- `data/universe_nasdaq100.json` — 默认股票池与来源
- `references/` — 打分规则与原则清单
- `docs/demo.md` — 实测完整榜单

## 已知数据边界

- 部分公司对东财美股财务接口无覆盖（脚本会明确报错并继续跑其余标的），保险类公司尤其常见。
- 多重投票权/含点号的代码写法特殊：伯克希尔需写 `BRK.B`。
- 财年截止日不统一（微软 6 月、英伟达 1 月、苹果 9 月），只做公司自身历史比较，不做跨行业横向对齐。

## 免责声明

仅供学习研究，不构成投资建议。财务数据来自第三方公开接口，可能存在缺失、滞后或重述；进入决策前请回到 SEC EDGAR 的 10-K / 10-Q 核对原文。
