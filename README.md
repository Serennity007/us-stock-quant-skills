# us-stock-quant-skills

**[中文](README.md) | [English](README.en.md) | [日本語](README.ja.md)**

![License](https://img.shields.io/badge/License-MIT-blue)
![Data](https://img.shields.io/badge/data-akshare-lightgrey)

美股量化 / 选股 AI Skill 合集：把可复现的筛选与打分逻辑写成脚本，把判断框架写成文档，供 Claude Code 与通用 Agent Skills 目录加载。全部数据来自公开接口，无需 API key。

- **免责声明**：本仓库内容仅供学习研究，不构成任何投资建议。股市有风险，投资需谨慎。所有结论依赖第三方公开数据，可能存在缺失、滞后或重述，决策前请回到 SEC EDGAR 的 10-K / 10-Q 核对原文。
- **收录日期**：2026-10-11。

## 使用说明

把需要的技能目录复制到你的技能目录即可：

```bash
# Claude Code
cp -r buffett-value-investing-us ~/.claude/skills/

# 或通用 agents skills 目录
cp -r buffett-value-investing-us ~/.agents/skills/
```

依赖：`pip install akshare pandas`（Python ≥ 3.9，无需任何 API key）。

## 已收录技能

| 技能 | 做什么 | 数据源 |
|---|---|---|
| [buffett-value-investing-us](buffett-value-investing-us) | 巴菲特式价值投资：连续 5 年 ROE/毛利率/负债率/经营现金流门槛 + PE/PB 自身五年分位，含股票池打分与单票深度分析 | akshare（东方财富美股财务指标、现金流量表；新浪美股日线） |

每个技能目录结构一致：

```
<skill>/
├── SKILL.md              # 技能定义（Agent 加载入口）
├── README.md/.en/.ja     # 三语说明
├── scripts/              # 可直接运行的脚本
├── references/           # 打分规则 + 判断框架
├── data/                 # 静态数据（含来源与抓取日期）
└── docs/demo.md          # 实测输出
```

## 数据与来源

- **行情与财务**：[akshare](https://github.com/akfamily/akshare) 公开接口（东方财富、新浪财经）。所有脚本对每次调用做指数退避重试，单只失败不阻断整轮，并在结尾汇总失败清单。
- **股票池**：`buffett-value-investing-us/data/universe_nasdaq100.json` 取自 Nasdaq 官方接口 `api.nasdaq.com/api/quote/list-type/nasdaq100`，成分截至 **2026-10-09**、抓取于 **2026-10-11**。成分股按季度调整，本仓库不会自动同步；可直接改用 `--tickers`。
- **已知接口边界**：美股没有「全市场成分股 + 逐日历史估值」两类接口（A 股版有）。因此股票池是静态清单，PE/PB 分位由日线价与财年 EPS/ROE 自行构造，属近似值——技能文档中已逐条说明。

## 路线图

当前只有 1 个旗舰技能，先把数据层与打分口径跑稳。后续按同一模板增加：动量/相对强度（CANSLIM）、市场周期温度计、宏观仪表盘等美股版本。命名一律带 `-us` 后缀，避免与 A 股技能在安装目录中重名冲突。

## License

[MIT](LICENSE)，© 2026 Serennity007。代码与本仓库整理内容按 MIT 授权；akshare 与其上游数据源的条款各自适用。
