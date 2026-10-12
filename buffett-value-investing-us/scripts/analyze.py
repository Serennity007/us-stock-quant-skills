#!/usr/bin/env python3
"""analyze.py — 对单只美股做巴菲特式完整分析。

用法:
    python scripts/analyze.py --ticker MSFT
    python scripts/analyze.py --ticker COST --years 5 --out msft.md

输出: 财年趋势、巴菲特门槛逐项判定、PE/PB 五年分位与参考价、护城河人工清单。
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
    from screen import (YEARS, _retry_call, annual_indicators, numeric, valuation_percentiles,
                        OCF_ITEM, _friendly)
    import akshare as ak
except ImportError as e:
    sys.exit(f"ERROR: 需要与本脚本同目录的 screen.py，以及 akshare/pandas（{e}）\n先执行: pip install akshare pandas")

YI = 1e8  # 亿美元


def ocf_series(ticker: str, years: int) -> pd.DataFrame:
    """近 N 个财年经营现金流净额（美元）。取不到返回空表。"""
    try:
        df = _retry_call(lambda: ak.stock_financial_us_report_em(stock=ticker, symbol="现金流量表", indicator="年报"))
    except Exception as e:
        print(f"提示: 现金流量表取数失败（{ _friendly(e) }），经营现金流一列将缺失。", file=sys.stderr)
        return pd.DataFrame(columns=["REPORT_DATE", "value"])
    if df is None or df.empty or "ITEM_NAME" not in df.columns:
        return pd.DataFrame(columns=["REPORT_DATE", "value"])
    rows = df[df["ITEM_NAME"].astype(str).str.strip() == OCF_ITEM].copy()
    rows["value"] = pd.to_numeric(rows["AMOUNT"], errors="coerce")
    rows["REPORT_DATE"] = pd.to_datetime(rows["REPORT_DATE"], errors="coerce")
    rows = rows.dropna(subset=["value", "REPORT_DATE"]).sort_values("REPORT_DATE")
    return rows.drop_duplicates(subset=["REPORT_DATE"], keep="last").tail(years)


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


def gate(label: str, passed: bool, detail: str) -> str:
    return f"| {label} | {'✅ 通过' if passed else '❌ 未过'} | {detail} |"


def main():
    ap = argparse.ArgumentParser(description="巴菲特式美股单票分析")
    ap.add_argument("--ticker", required=True, help="美股代码，如 MSFT（伯克希尔需写 BRK.B）")
    ap.add_argument("--years", type=int, default=YEARS, help=f"回看财年数（默认 {YEARS}）")
    ap.add_argument("--out", default=None, help="把报告另存为 Markdown 的路径（可选）")
    args = ap.parse_args()
    ticker = args.ticker.strip().upper()

    ind = annual_indicators(ticker).tail(args.years)
    px = price_history(ticker, args.years)
    time_col = "REPORT_DATE"
    ind = ind.assign(**{time_col: pd.to_datetime(ind[time_col], errors="coerce")}).sort_values(time_col)

    roe = numeric(ind, "ROE_AVG")
    gross = numeric(ind, "GROSS_PROFIT_RATIO")
    debt = numeric(ind, "DEBT_ASSET_RATIO")
    eps = numeric(ind, "BASIC_EPS")
    ocf = ocf_series(ticker, args.years)

    price = float(px["close"].iloc[-1])
    pe_pct, pb_pct = valuation_percentiles(ticker, ind)
    pe_now = price / float(eps.iloc[-1]) if len(eps) and eps.iloc[-1] > 0 else None

    lines = []
    add = lines.append
    add(f"# {ticker} 巴菲特式分析")
    add("")
    add(f"- 数据截至：行情 {px['date'].max().date()}（未复权收盘 {price:.2f} 美元）；财报期 {ind[time_col].iloc[-1].date()}")
    add(f"- 覆盖财年数：{len(ind)}（要求 {args.years}）")
    add(f"- 数据源：akshare 东方财富美股财务指标 / 现金流量表 / 新浪美股日线")
    add("")
    add("## 近 %d 财年趋势" % len(ind))
    add("")
    add("| 财年截止 | 营收(亿美元) | 归母净利(亿美元) | 毛利率% | ROE% | 资产负债率% | 经营现金流(亿美元) | 基本EPS |")
    add("|---|---|---|---|---|---|---|---|")
    ocf_map = {r["REPORT_DATE"].date(): r["value"] for _, r in ocf.iterrows()} if not ocf.empty else {}
    for _, row in ind.iterrows():
        d = row[time_col].date()
        def fmt(v, div=1, digits=1):
            n = pd.to_numeric(v, errors="coerce")
            return "—" if pd.isna(n) else f"{float(n) / div:,.{digits}f}"
        ocf_v = ocf_map.get(d)
        add("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            d, fmt(row.get("OPERATE_INCOME"), YI), fmt(row.get("PARENT_HOLDER_NETPROFIT"), YI),
            fmt(row.get("GROSS_PROFIT_RATIO")), fmt(row.get("ROE_AVG")), fmt(row.get("DEBT_ASSET_RATIO")),
            "—" if ocf_v is None else f"{ocf_v / YI:,.1f}", fmt(row.get("BASIC_EPS"), digits=2)))
    add("")
    add("## 巴菲特门槛逐项判定")
    add("")
    add("| 标准 | 判定 | 依据 |")
    add("|---|---|---|")
    if len(roe):
        n_pass = int((roe > 15).sum())
        add(gate(f"ROE 连续 {args.years} 年 > 15%", n_pass >= len(roe) and len(roe) >= args.years,
                 f"{n_pass}/{len(roe)} 年达标；区间 {roe.min():.1f}%–{roe.max():.1f}%"))
    if len(gross):
        spread = gross.max() - gross.min()
        add(gate("毛利率 > 30% 且五年波动 < 5pp", bool(gross.mean() > 30 and spread < 5),
                 f"均值 {gross.mean():.1f}%，极差 {spread:.1f}pp"))
    if len(debt):
        latest = float(debt.iloc[-1])
        add(gate("资产负债率 < 50%（金融股需人工剔除）", latest < 50,
                 f"最新 {latest:.1f}%；银行/保险类此指标不适用"))
    if len(ocf):
        pos = int((ocf["value"] > 0).sum())
        add(gate(f"经营现金流连续 {args.years} 年为正", pos >= args.years and len(ocf) >= args.years,
                 f"{pos}/{len(ocf)} 年为正"))
    else:
        add("| 经营现金流 | ⚠️ 缺数据 | 现金流量表未取到，需人工核对 |")
    if pe_pct is not None:
        add(gate("PE 处于近五年低位（< 30% 分位）", pe_pct < 0.3, f"当前分位 {pe_pct:.2f}"))
    if pb_pct is not None:
        add(gate("PB 处于近五年低位（< 30% 分位）", pb_pct < 0.3, f"当前分位 {pb_pct:.2f}"))
    add("")
    add("## 估值参考")
    add("")
    if pe_now:
        add(f"- 当前 PE（对最新财年基本 EPS）：**{pe_now:.1f} 倍**")
    if pe_pct is not None and pe_now:
        p30, p50 = float(hist_quantile(px, eps, ind, 0.30)), float(hist_quantile(px, eps, ind, 0.50))
        add(f"- 近五年 PE 分位：{pe_pct:.2f}；30% 分位对应约 {p30:.1f} 倍、50% 分位约 {p50:.1f} 倍")
        add(f"- 以最新 EPS 折算的参考价：30% 分位 ≈ **{p30 * float(eps.iloc[-1]):.2f} 美元**，50% 分位 ≈ {p50 * float(eps.iloc[-1]):.2f} 美元")
        add(f"- 现价 {price:.2f} 美元相对 30% 分位参考价的安全边际：{(p30 * float(eps.iloc[-1]) / price - 1) * 100:+.1f}%")
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
        "任何决策请以公司公告原文与自身独立判断为准。")

    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"已写入 {args.out}", file=sys.stderr)


def hist_quantile(px: pd.DataFrame, eps: pd.Series, ind: pd.DataFrame, q: float):
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
    return pd.Series(series).quantile(q)


if __name__ == "__main__":
    main()
