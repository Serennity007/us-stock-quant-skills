---
name: buffett-value-investing-us
description: 美股巴菲特式价值投资分析：护城河评估、连续5年ROE/毛利率/负债率/经营现金流筛选、PE/PB 五年分位与安全边际 | US-stock Buffett-style value investing analysis: moat assessment, 5-year ROE/gross-margin/debt/operating-cash-flow screen, 5-year PE/PB percentile and margin-of-safety | 米国株バフェット式バリュー投資分析：堀評価、5年連続ROE/粗利率/負債比率/営業キャッシュフローのスクリーニング、PE/PB五年分位と安全余裕
author: Serennity007
license: MIT
---

# 巴菲特式价值投资（美股）

用巴菲特的框架在美股做两件事：

1. **筛股**（`scripts/screen.py`）：对股票池（默认随仓库附带的 NASDAQ-100 清单，也可 `--tickers` 自定义）逐只打分排序，筛出符合巴菲特财务门槛的候选。
2. **分析**（`scripts/analyze.py`）：对单只股票输出近 5 财年趋势、门槛逐项判定、PE/PB 五年分位与参考价、护城河人工清单。

数据来自 akshare 的美股接口（东方财富财务指标与现金流量表、新浪美股日线）。

## 筛选标准（巴菲特财务门槛）

| 维度 | 标准 | 数据字段 |
|---|---|---|
| ROE | 连续 5 年 > 15% | `ROE_AVG`（年报） |
| 毛利率 | 5 年稳定（极差 < 5pp）且均值 > 30% | `GROSS_PROFIT_RATIO` |
| 资产负债率 | < 50%（金融股不适用，需人工剔除） | `DEBT_ASSET_RATIO` |
| 自由现金流 | 连续 5 年为正（FCF = 经营现金流净额 + 购买固定资产） | 现金流量表两项同取 |
| 估值 | PE / PB 处于近 5 年分位低位 | 日线收盘价 × 财年 EPS / ROE 自行构造 |

打分权重、判定线（**≥80 进人工护城河核查 / 60–79 有短板 / <60 不符合**）与失真处理见 `references/scoring_rules.md`，投资原则见 `references/buffett_principles.md`。

## 快速开始

```bash
pip install akshare pandas

# 默认股票池（NASDAQ-100，101 只，含来源与日期）
python scripts/screen.py --top 20 --out result.csv

# 只跑自选清单
python scripts/screen.py --tickers MSFT,COST,PEP,ADBE

# 单票深度分析
python scripts/analyze.py --ticker MSFT
python scripts/analyze.py --ticker COST --out cost.md
```

## 失真处理（美股特有）

回购把股东权益买薄甚至买成负数时，ROE 与 PB 会同时失真（实测 BKNG 的 ROE 峰值 22,573%、ORLY 5,863%）。脚本用「资产负债率 ≥ 100% ⇔ 权益 ≤ 0」判定，命中后 **ROE 与负债率记 N/A、PB 分位置空，整只逐出主榜单单列人工判断**，既不白送分也不误罚。权益为正但 ROE > 100%（如 NVDA）属真实盈利，仍参与排名，只是停用 PB 分位。

## 与 A 股版的三处关键差异

1. **没有全市场成分股接口**：A 股版可拉沪深300 成分股，美股的 `stock_us_spot_em` 在部分网络环境不可达，因此本技能改为随仓库附带一份带来源与日期的静态清单（`data/universe_nasdaq100.json`），并支持 `--tickers` 覆盖。成分股会季度调整，请定期更新该文件。
2. **没有每日历史估值接口**：A 股版直接查 `stock_value_em` 拿 PE/PB 序列，美股需自己构造——日 PE = 收盘价 ÷ 当年基本 EPS，日 PB = 日 PE × 当年 ROE（因 P/B = P/E × E/B 为恒等式）。近似点在于假定财年内 EPS/ROE 不变、且不考虑财报发布滞后，因此分位是**近似值**，输出中已注明。
3. **现金流口径与失真处理已按美股重定**：改用自由现金流，股东权益 ≤ 0 记 N/A 并逐出排名，判定线由 70 抬到 80。**因此本技能分数与 A 股版不再直接可比**，不要跨市场横向对照；理由与实测数据见 `references/scoring_rules.md`。

## 已知数据边界

- 部分公司对东财美股财务接口无覆盖（脚本会明确报「接口无该代码的年度财务数据」并继续跑其余标的），例如某些保险公司。
- 含 A/B 股或多种投票权结构的代码写法与常见 ticker 不同（伯克希尔需写 `BRK.B`）。
- 财年截止日不统一（微软 6 月、英伟达 1 月、苹果 9 月），跨年比较时以公司自身历史为基准，不做跨行业横向对齐。

## 免责声明

仅供学习研究，不构成投资建议。财务数据来自第三方公开接口，可能存在缺失、滞后或重述。
