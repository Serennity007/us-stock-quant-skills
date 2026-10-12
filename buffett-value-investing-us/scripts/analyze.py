#!/usr/bin/env python3
"""analyze.py — 对单只美股做巴菲特式完整分析。

用法:
    python scripts/analyze.py --ticker MSFT
    python scripts/analyze.py --ticker COST --years 5 --out cost.md

输出: 财年趋势、巴菲特门槛逐项判定、PE/PB 五年分位与参考价、护城河人工清单。
股东权益 ≤ 0（回购所致）时，ROE 与 PB 会被标为不适用而不是按高分处理。
数据源: akshare（东方财富美股财务指标 / 现金流量表 / 新浪财经美股日线）。
"""
import os

os.environ.setdefault("TQDM_DISABLE", "1")

import argparse
import sys
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from screen import (YEARS, OCF_ITEM, CAPEX_ITEM, NEGATIVE_EQUITY_DEBT_PCT, PASS_LINE, WATCH_LINE,
                        _friendly, _retry_call, annual_indicators, numeric, valuation_percentiles)
    import akshare as ak
except ImportError as e:
    sys.exit(f"ERROR: 需要与本脚本同目录的 screen.py，以及 akshare/pandas（{e}）\n先执行: pip install akshare pandas")

YI = 1e8  # 亿美元


def cashflow_frame(ticker: str, years: int) -> pd.DataFrame:
    """近 N 个财年的经营现金流、资本开支与自由现金流（美元）。取不到返回空表。"""
    try:
        df = _retry_call(lambda: ak.stock_financial_us_report_em(stock=ticker, symbol="现金流量表", indicator="年报"))
    except Exception as e:
        print(f"提示: 现金流量表取数失败（{_friendly(e)}），现金流两列将缺失。", file=sys.stderr)
        return pd.DataFrame(columns=["REPORT_DATE", "ocf", "capex", "fcf"])
    if df is None or df.empty or "ITEM_NAME" not in df.columns:
        return pd.DataFrame(columns=["REPORT_DATE", "ocf", "capex", "fcf"])
    rows = df[df["ITEM_NAME"].astype(str).str.strip().isin([OCF_ITEM, CAPEX_ITEM])].copy()
    if rows.empty:
        return pd.DataFrame(columns=["REPORT_DATE", "ocf", "capex", "fcf"])
    rows["value"] = pd.to_numeric(rows["AMOUNT"], errors="coerce")
    rows["REPORT_DATE"] = pd.to_datetime(rows["REPORT_DATE"], errors="coerce")
    rows = rows.dropna(subset=["value", "REPORT_DATE"])
    wide = rows.pivot_table(index="REPORT_DATE", columns="ITEM_NAME", values="value", aggfunc="last")
    wide = wide.rename(columns={OCF_ITEM: "ocf", CAPEX_ITEM: "capex"}).sort_index()
    if "capex" not in wide.columns:
        wide["capex"] = 0.0
    wide["fcf"] = wide["ocf"] + wide["capex"].fillna(0.0)
    return wide.tail(years).reset_index()


def price_history(ticker: str, years: int) -> pd.DataFrame:
    try:
        px = _retry_call(lambda: ak.stock_us_daily(symbol=ticker, adjust=""))
    except Exception as e:
        raise RuntimeError(f"获取 {ticker} 日线失败: {_friendly(e)}")
    if px is None or px.empty:
        raise RuntimeError(f"获取 {ticker} 日线为空")
    px = px.copy()
    px["date"] = pd.to_datetime(px["date"], errors="coerce")
    px["close"] = pd.to_numeric(px["close"], errors="coerce")
    px = px.dropna(subset=["date", "close"]).sort_values("date")
    return px[px["date"] >= px["date"].max() - pd.Timedelta(days=365 * years)]


def hist_quantile(px: pd.DataFrame, ind: pd.DataFrame, q: float):
    """近五年 PE 序列的指定分位。"""
    series = []
    for _, row in ind.iterrows():
        e = pd.to_numeric(row.get("BASIC_EPS"), errors="coerce")
        if pd.isna(e) or e <= 0:
            continue
        year = pd.Timestamp(row["REPORT_DATE"]).year
        seg = px[(px["date"].dt.year == year) | ((px["date"].dt.year == year + 1) & (px["date"].dt.month <= 6))]
        series.extend((seg["close"] / float(e)).tolist())
    if len(series) < 60:
        return float("nan")
    return float(pd.Series(series).quantile(q))


def gate(label: str, passed, detail: str) -> str:
    mark = "✅ 通过" if passed is True else ("⚠️ 不适用" if passed is None else "❌ 未过")
    return f"| {label} | {mark} | {detail} |"


def main():
    ap = argparse.ArgumentParser(description="巴菲特式美股单票分析")
    ap.add_argument("--ticker", required=True, help="美股代码，如 MSFT（伯克希尔需写 BRK.B）")
    ap.add_argument("--years", type=int, default=YEARS, help=f"回看财年数（默认 {YEARS}）")
    ap.add_argument("--out", default=None, help="把报告另存为 Markdown 的路径（可选）")
    args = ap.parse_args()
    ticker = args.ticker.strip().upper()

    ind = annual_indicators(ticker).tail(args.years)
    px = price_history(ticker, args.years)
    ind = ind.assign(REPORT_DATE=pd.to_datetime(ind["REPORT_DATE"], errors="coerce")).sort_values("REPORT_DATE")

    roe = numeric(ind, "ROE_AVG")
    gross = numeric(ind, "GROSS_PROFIT_RATIO")
    debt = numeric(ind, "DEBT_ASSET_RATIO")
    eps = numeric(ind, "BASIC_EPS")
    cf = cashflow_frame(ticker, args.years)

    price = float(px["close"].iloc[-1])
    debt_latest = float(debt.iloc[-1]) if len(debt) else None
    # 负债率 ≥ 100% ⇔ 股东权益 ≤ 0：ROE 分母趋零而失真，PB 恒等式也随之失效，
    # 负债率本身也不再代表杠杆风险（这类公司常是净现金）。
    equity_negative = debt_latest is not None and debt_latest >= NEGATIVE_EQUITY_DEBT_PCT

    pe_pct, pb_pct = valuation_percentiles(ticker, ind)
    if equity_negative:
        pb_pct = None
    pe_now = price / float(eps.iloc[-1]) if len(eps) and eps.iloc[-1] > 0 else None

    lines = []
    add = lines.append
    add(f"# {ticker} 巴菲特式分析")
    add("")
    add(f"- 数据截至：行情 {px['date'].max().date()}（未复权收盘 {price:.2f} 美元）；财报期 {ind['REPORT_DATE'].iloc[-1].date()}")
    add(f"- 覆盖财年数：{len(ind)}（要求 {args.years}）")
    add("- 数据源：akshare 东方财富美股财务指标 / 现金流量表 / 新浪美股日线")
    if equity_negative:
        add(f"- ⚠️ **股东权益疑似 ≤ 0**（资产负债率 {debt_latest:.1f}%）：ROE 与 PB 均不适用，"
            "本报告中这两项不计分、不判定。这类公司往往是长期回购所致，需回到资产负债表原值人工核查。")
    add("")
    add("## 近 %d 财年趋势" % len(ind))
    add("")
    add("| 财年截止 | 营收(亿美元) | 归母净利(亿美元) | 毛利率% | ROE% | 资产负债率% | 经营现金流(亿美元) | 资本开支(亿美元) | 自由现金流(亿美元) | 基本EPS |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    cf_map = {r["REPORT_DATE"].date(): r for _, r in cf.iterrows()} if not cf.empty else {}

    def num(v, digits=1):
        n = pd.to_numeric(v, errors="coerce")
        return "—" if pd.isna(n) else f"{float(n):,.{digits}f}"

    for _, row in ind.iterrows():
        d = row["REPORT_DATE"].date()
        c = cf_map.get(d)
        ocf = num(c["ocf"] / YI) if c is not None and pd.notna(c.get("ocf")) else "—"
        capex = num(c["capex"] / YI) if c is not None and pd.notna(c.get("capex")) else "—"
        fcf = num(c["fcf"] / YI) if c is not None and pd.notna(c.get("fcf")) else "—"
        add("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            d, num(pd.to_numeric(row.get("OPERATE_INCOME"), errors="coerce") / YI),
            num(pd.to_numeric(row.get("PARENT_HOLDER_NETPROFIT"), errors="coerce") / YI),
            num(row.get("GROSS_PROFIT_RATIO")), num(row.get("ROE_AVG")), num(row.get("DEBT_ASSET_RATIO")),
            ocf, capex, fcf, num(row.get("BASIC_EPS"), 2)))
    add("")
    add("## 巴菲特门槛逐项判定")
    add("")
    add("| 标准 | 判定 | 依据 |")
    add("|---|---|---|")
    if len(roe):
        n_pass = int((roe > 15).sum())
        add(gate(f"ROE 连续 {args.years} 年 > 15%",
                 None if equity_negative else (n_pass >= len(roe) and len(roe) >= args.years),
                 f"权益 ≤ 0，指标失真，不适用" if equity_negative else f"{n_pass}/{len(roe)} 年达标；区间 {roe.min():.1f}%–{roe.max():.1f}%"))
    if len(gross):
        spread = gross.max() - gross.min()
        add(gate("毛利率 > 30% 且五年极差 < 5pp", bool(gross.mean() > 30 and spread < 5),
                 f"均值 {gross.mean():.1f}%，极差 {spread:.1f}pp"))
    if debt_latest is not None:
        add(gate("资产负债率 < 50%（金融股不适用）",
                 None if equity_negative else debt_latest < 50,
                 f"最新 {debt_latest:.1f}%" + ("；权益 ≤ 0，此值不反映杠杆风险" if equity_negative else "")))
    if not cf.empty and "fcf" in cf.columns:
        pos = int((cf["fcf"] > 0).sum())
        add(gate(f"自由现金流连续 {args.years} 年为正", pos >= args.years and len(cf) >= args.years,
                 f"{pos}/{len(cf)} 年为正；最新一年 {cf['fcf'].iloc[-1] / YI:,.1f} 亿美元"))
    else:
        add("| 自由现金流 | ⚠️ 缺数据 | 现金流量表未取到，需人工核对 |")
    if pe_pct is not None:
        add(gate("PE 处于近五年低位（< 30% 分位）", pe_pct < 0.3, f"当前分位 {pe_pct:.2f}"))
    if pb_pct is not None:
        add(gate("PB 处于近五年低位（< 30% 分位）", pb_pct < 0.3, f"当前分位 {pb_pct:.2f}"))
    elif equity_negative:
        add("| PB 分位 | ⚠️ 不适用 | 权益 ≤ 0 时 PB = PE × ROE 失效 |")
    elif len(roe) and float(roe.max()) > 100:
        add("| PB 分位 | ⚠️ 不适用 | ROE > 100%（薄权益），乘出的 PB 失真；ROE 本身为真实盈利，仍参与打分 |")
    add("")
    add("## 估值参考")
    add("")
    if pe_now:
        add(f"- 当前 PE（对最新财年基本 EPS）：**{pe_now:.1f} 倍**")
    if pe_pct is not None and pe_now and len(eps):
        p30, p50 = hist_quantile(px, ind, 0.30), hist_quantile(px, ind, 0.50)
        anchor = float(eps.iloc[-1])
        add(f"- 近五年 PE 分位：{pe_pct:.2f}；30% 分位约 {p30:.1f} 倍、50% 分位约 {p50:.1f} 倍")
        add(f"- 以最新 EPS 折算的参考价：30% 分位 ≈ **{p30 * anchor:.2f} 美元**，50% 分位 ≈ {p50 * anchor:.2f} 美元")
        add(f"- 现价 {price:.2f} 美元相对 30% 分位参考价：{(p30 * anchor / price - 1) * 100:+.1f}%")
    else:
        add("- 估值分位数据不足（EPS 非正或日线历史太短），不给出参考价。")
    add("")
    add("## 护城河清单（人工判断，脚本不打分）")
    add("")
    for item in ["无形资产（品牌 / 专利 / 牌照）", "转换成本（客户换供应商的代价）",
                 "网络效应", "成本或规模优势", "准入地理或监管位置"]:
        add(f"- [ ] {item}：")
    add("")
    add("## 免责声明")
    add("")
    add("仅供学习研究，不构成投资建议。财务口径来自第三方公开接口，可能存在缺失、滞后或重述；"
        "PE/PB 分位由「财年内 EPS 与 ROE 保持不变」的近似算法构造，与逐日真实值有偏差。"
        f"打分判定线：≥{PASS_LINE} 进入人工护城河核查，{WATCH_LINE}–{PASS_LINE - 1} 有短板，<{WATCH_LINE} 不符合框架。"
        "任何决策请以公司公告原文与自身独立判断为准。")

    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"已写入 {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
