#!/usr/bin/env python3
"""screen.py — 巴菲特标准美股初筛（NASDAQ-100 股票池或自选清单）。

用法:
    python scripts/screen.py                      # 默认跑 data/universe_nasdaq100.json
    python scripts/screen.py --top 20 --out result.csv
    python scripts/screen.py --tickers NVDA,MSFT,COST

数据源: akshare（东方财富美股财务指标 / 现金流量表 / 新浪财经美股日线）。
打分规则见 references/scoring_rules.md，与 A 股版 buffett-value-investing 同口径。
"""
import os

os.environ.setdefault("TQDM_DISABLE", "1")

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import akshare as ak
except ImportError:
    sys.exit("ERROR: 未安装 akshare，请先执行: pip install akshare pandas")

YEARS = 5
OCF_ITEM = "经营活动产生的现金流量净额"
CAPEX_ITEM = "购买固定资产"
# 股东权益 ≤ 0 的判据：资产负债率 ≥ 100%（负债总额超过资产总额）。
# 回购把权益买成负数时，ROE 与 PB 都会失真（分母趋零），不能当成"优秀"打分。
NEGATIVE_EQUITY_DEBT_PCT = 100.0
# ROE 高于此值同样视为失真（权益过薄），不用于构造 PB。
ROE_SANITY_CAP = 100.0
PASS_LINE = 80
WATCH_LINE = 60
DEFAULT_UNIVERSE = Path(__file__).resolve().parent.parent / "data" / "universe_nasdaq100.json"


def _friendly(err) -> str:
    """东方财富对无覆盖的美股代码会返回 None，akshare 内部随即抛 NoneType 下标错误。"""
    text = str(err)
    if "NoneType" in text and "subscript" in text:
        return "接口无该代码的年度财务数据（可能未覆盖、已退市或代码写法不同，如 BRK-B 需写成 BRK.B）"
    return text


def _retry_call(func, max_retries: int = 3, sleep_base: float = 1.0):
    """带指数退避的简单重试，最后一次失败抛出原异常。"""
    last_err = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(sleep_base * (2 ** attempt))
    raise last_err


def annual_indicators(ticker: str) -> pd.DataFrame:
    """近 YEARS 个财年的年度主要财务指标，按报告期升序。失败抛异常。"""
    try:
        df = _retry_call(lambda: ak.stock_financial_us_analysis_indicator_em(symbol=ticker, indicator="年报"))
    except Exception as e:
        raise RuntimeError(f"获取 {ticker} 财务指标失败: {_friendly(e)}")
    if df is None or df.empty:
        raise RuntimeError(f"获取 {ticker} 财务指标为空（可能接口限流或代码有误）")
    df.columns = [str(c).strip() for c in df.columns]
    if "REPORT_DATE" not in df.columns:
        raise RuntimeError(f"{ticker} 返回格式变化，缺少 REPORT_DATE 列")
    df["REPORT_DATE"] = pd.to_datetime(df["REPORT_DATE"], errors="coerce")
    df = df.dropna(subset=["REPORT_DATE"]).sort_values("REPORT_DATE")
    # 同一财年可能重复披露，保留最新一次
    df = df.drop_duplicates(subset=["REPORT_DATE"], keep="last").tail(YEARS)
    if df.empty:
        raise RuntimeError(f"{ticker} 无年度财务数据")
    return df


def numeric(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce").dropna()


def fcf_positive_years(ticker: str):
    """近 YEARS 个财年自由现金流为正的年数，以及最新一年的 FCF（美元）。

    A 股版用「经营现金流为正」是因为占款与应收造假常见；美股大型公司几乎不可能连续
    五年经营现金流为负——实测 90% 的标的拿满这 20 分，零区分度。改用 FCF（经营现金流
    净额 + 购买固定资产，后者接口内已为负值）后，资本开支吃掉现金流的公司才会被区分。
    """
    try:
        df = _retry_call(lambda: ak.stock_financial_us_report_em(stock=ticker, symbol="现金流量表", indicator="年报"))
    except Exception:
        return 0, None
    if df is None or df.empty or "ITEM_NAME" not in df.columns:
        return 0, None
    rows = df[df["ITEM_NAME"].astype(str).str.strip().isin([OCF_ITEM, CAPEX_ITEM])].copy()
    if rows.empty:
        return 0, None
    rows["value"] = pd.to_numeric(rows["AMOUNT"], errors="coerce")
    rows["REPORT_DATE"] = pd.to_datetime(rows["REPORT_DATE"], errors="coerce")
    rows = rows.dropna(subset=["value", "REPORT_DATE"])
    wide = rows.pivot_table(index="REPORT_DATE", columns="ITEM_NAME", values="value", aggfunc="last")
    if OCF_ITEM not in wide.columns:
        return 0, None
    capex = wide[CAPEX_ITEM] if CAPEX_ITEM in wide.columns else pd.Series(0.0, index=wide.index)
    wide["fcf"] = wide[OCF_ITEM] + capex.fillna(0.0)
    recent = wide.sort_index().tail(YEARS)
    if recent.empty:
        return 0, None
    return int((recent["fcf"] > 0).sum()), float(recent["fcf"].iloc[-1])


def valuation_percentiles(ticker: str, ind: pd.DataFrame):
    """(PE 分位, PB 分位)，0-1；数据不足返回 None。

    美股没有 A 股 stock_value_em 那样的每日历史估值接口，这里自己构造：
      日 PE = 收盘价 / 当年基本每股收益；
      日 PB = 日 PE × 当年 ROE（因为 P/B = P/E × E/B，恒等）。
    近似之处：财年 EPS/ROE 在该财年内保持不变，且不考虑报告发布滞后。
    """
    eps = numeric(ind, "BASIC_EPS")
    roe = numeric(ind, "ROE_AVG")
    if ind.empty or eps.empty:
        return None, None
    try:
        px = _retry_call(lambda: ak.stock_us_daily(symbol=ticker, adjust=""))
    except Exception:
        return None, None
    if px is None or px.empty or "close" not in px.columns:
        return None, None
    px = px.copy()
    px["date"] = pd.to_datetime(px["date"], errors="coerce")
    px["close"] = pd.to_numeric(px["close"], errors="coerce")
    px = px.dropna(subset=["date", "close"]).sort_values("date")
    px = px[px["date"] >= px["date"].max() - pd.Timedelta(days=365 * YEARS)]
    if len(px) < 60:
        return None, None

    frames = []
    for i, row in ind.iterrows():
        year = pd.Timestamp(row["REPORT_DATE"]).year
        e = pd.to_numeric(row.get("BASIC_EPS"), errors="coerce")
        r = pd.to_numeric(row.get("ROE_AVG"), errors="coerce")
        if pd.isna(e) or e <= 0:
            continue
        seg = px[(px["date"].dt.year == year) | ((px["date"].dt.year == year + 1) & (px["date"].dt.month <= 6))]
        if seg.empty:
            continue
        pe = seg["close"] / float(e)
        # PB = PE × ROE 是恒等式，但输入失真时结果也失真：权益被回购买成接近零
        # 会让 ROE 出现 5,000% 甚至 22,000% 这种读数（实测 BKNG、ORLY、MAR），
        # 乘出来的 PB 分位毫无意义，因此只接受 0 < ROE ≤ ROE_SANITY_CAP。
        pb = pe * (float(r) / 100) if pd.notna(r) and 0 < float(r) <= ROE_SANITY_CAP else float("nan")
        frames.append(pd.DataFrame({"date": seg["date"], "pe": pe, "pb": pb}))
    if not frames:
        return None, None
    hist = pd.concat(frames, ignore_index=True).sort_values("date").dropna(subset=["pe"])
    if len(hist) < 60:
        return None, None
    current_pe = float(hist["pe"].iloc[-1])
    pe_pct = float((hist["pe"] <= current_pe).mean())
    pb = hist["pb"].dropna()
    pb_pct = float((pb <= pb.iloc[-1]).mean()) if len(pb) >= 60 else None
    return pe_pct, pb_pct


def score_one(ticker: str) -> dict:
    ind = annual_indicators(ticker)
    time.sleep(0.15)

    roe = numeric(ind, "ROE_AVG")
    gross = numeric(ind, "GROSS_PROFIT_RATIO")
    debt = numeric(ind, "DEBT_ASSET_RATIO")

    # 资产负债率 ≥ 100% ⇔ 负债总额超过资产总额 ⇔ 股东权益 ≤ 0。
    # 此时 ROE 的分母趋零（实测 BKNG 峰值 22,573%、ORLY 5,863%、MAR 237%），
    # 既不该按「优秀」白送 30 分，也不该按「高杠杆」把负债率判 0 分——
    # Booking、O'Reilly 这类其实是净现金公司。两项一律记 N/A。
    debt_latest = round(float(debt.iloc[-1]), 1) if len(debt) else None
    equity_negative = debt_latest is not None and debt_latest >= NEGATIVE_EQUITY_DEBT_PCT
    thin_equity = (not equity_negative) and len(roe) > 0 and float(roe.max()) > ROE_SANITY_CAP
    # 两档处理，不要混为一谈：
    #   权益 ≤ 0（BKNG/ORLY/SBUX）→ 三项失真，整只逐出排名，交人工判断；
    #   权益为正但 ROE > 100%（NVDA）→ ROE 是真实盈利能力，照常计分，只是不能用它推 PB。
    flag = "权益≤0，ROE/负债率/PB 均不适用" if equity_negative else ""
    note = "ROE>100%，PB 不适用" if thin_equity else ""

    if equity_negative:
        roe_score = 0
    else:
        roe_score = sum(6 if v > 15 else (3 if v > 12 else 0) for v in roe)

    gross_score = 0
    if len(gross):
        mean_g = gross.mean()
        gross_score += 10 if mean_g > 40 else (6 if mean_g > 30 else 0)
        spread = gross.max() - gross.min()
        gross_score += 10 if spread < 5 else (5 if spread < 10 else 0)

    if equity_negative:
        debt_score = 0
    else:
        debt_score = 0 if debt_latest is None else (
            15 if debt_latest < 40 else (8 if debt_latest < 50 else (3 if debt_latest < 65 else 0)))

    cf_years, fcf_latest = fcf_positive_years(ticker)
    cf_score = min(cf_years, YEARS) * 4
    time.sleep(0.15)

    pe_pct, pb_pct = valuation_percentiles(ticker, ind)
    if equity_negative or thin_equity:
        pb_pct = None
    val_score = 0
    if pe_pct is not None:
        val_score += 8 if pe_pct < 0.3 else (4 if pe_pct < 0.5 else 0)
    if pb_pct is not None:
        val_score += 7 if pb_pct < 0.3 else (3 if pb_pct < 0.5 else 0)

    total = roe_score + gross_score + debt_score + cf_score + val_score
    return {
        "ticker": ticker,
        "total": total,
        "flag": flag,
        "note": note,
        "roe_score": roe_score,
        "roe_annual": ",".join(f"{v:.1f}" for v in roe.tolist()) if len(roe) else "—",
        "gross_score": gross_score,
        "gross_mean": round(float(gross.mean()), 1) if len(gross) else None,
        "debt_score": debt_score,
        "debt_latest": debt_latest,
        "fcf_score": cf_score,
        "fcf_pos_years": cf_years,
        "fcf_latest_yi": round(fcf_latest / 1e8, 1) if fcf_latest is not None else None,
        "valuation_score": val_score,
        "pe_pct": round(pe_pct, 2) if pe_pct is not None else None,
        "pb_pct": round(pb_pct, 2) if pb_pct is not None else None,
        "data_years": int(len(roe)),
    }


def load_universe(path: Path) -> list:
    if not path.exists():
        sys.exit(f"ERROR: 找不到股票池文件 {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    companies = data["companies"] if isinstance(data, dict) else data
    return [x["symbol"] for x in companies if x.get("symbol")]


def main():
    ap = argparse.ArgumentParser(description="巴菲特标准美股初筛")
    ap.add_argument("--universe", default=str(DEFAULT_UNIVERSE), help="股票池 JSON 路径（默认 NASDAQ-100）")
    ap.add_argument("--tickers", default=None, help="逗号分隔的美股代码，优先于 --universe")
    ap.add_argument("--top", type=int, default=20, help="终端展示前 N 名")
    ap.add_argument("--out", default="screen_result.csv", help="CSV 输出路径")
    ap.add_argument("--sleep", type=float, default=0.3, help="每只股票间隔秒数（防限流）")
    args = ap.parse_args()

    if args.tickers:
        codes = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        codes = load_universe(Path(args.universe))
    print(f"股票池共 {len(codes)} 只，开始逐一打分（每只需 3 次接口调用，请耐心）...")

    rows, failed = [], []
    for i, code in enumerate(codes, 1):
        try:
            r = score_one(code)
            rows.append(r)
            print(f"[{i}/{len(codes)}] {code} 得分 {r['total']}")
        except Exception as e:
            failed.append((code, str(e)))
            print(f"[{i}/{len(codes)}] {code} 失败: {e}", file=sys.stderr)
        time.sleep(args.sleep)

    if not rows:
        sys.exit("ERROR: 全部股票获取失败，请检查网络或升级 akshare（pip install -U akshare）")

    df = pd.DataFrame(rows).sort_values("total", ascending=False)
    df.to_csv(args.out, index=False, encoding="utf-8-sig")

    # 指标失真的标的（股东权益 ≤ 0 等）不进主榜单排名：它们的 ROE 与负债率都是
    # N/A，留在榜里会既压低分数又误导排序，单列一节让人工判断。
    ranked = df[df["flag"] == ""]
    distorted = df[df["flag"] != ""]

    print(f"\n=== 前 {min(args.top, len(ranked))} 名（完整结果见 {args.out}）===")
    display_cols = ["ticker", "total", "roe_score", "gross_score", "debt_score",
                    "fcf_score", "valuation_score", "pe_pct", "pb_pct", "data_years"]
    display_df = ranked.head(args.top)[display_cols].copy()
    for c in ("pe_pct", "pb_pct"):
        display_df[c] = display_df[c].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    print(display_df.to_string(index=False))

    if not distorted.empty:
        print(f"\n=== 指标失真，未参与排名（{len(distorted)} 只）===")
        print(distorted[["ticker", "total", "gross_score", "fcf_score", "valuation_score",
                         "debt_latest", "flag"]].to_string(index=False))
        print("说明：股东权益 ≤ 0 时 ROE 与 PB 失去含义、负债率也不代表杠杆风险，需回到资产负债表原值人工判断。")

    noted = ranked[ranked["note"] != ""]
    if not noted.empty:
        print("\n以下标的 ROE > 100%（薄权益但为真实盈利，仍参与排名），但 PB 分位不适用：")
        print(", ".join(noted["ticker"].tolist()))

    incomplete = ranked[ranked["data_years"] < YEARS]
    if not incomplete.empty:
        print(f"\n注意: 以下 {len(incomplete)} 只财年数据不足 {YEARS} 年，分数参考性下降：")
        print(", ".join(incomplete["ticker"].tolist()))
    if failed:
        print(f"\n取数失败 {len(failed)} 只: {', '.join(t for t, _ in failed)}")
    print(f"\n成功 {len(rows)} 只（其中排名 {len(ranked)} 只、失真单列 {len(distorted)} 只），失败 {len(failed)} 只。")
    print(f"判定线: >={PASS_LINE} 进入人工护城河核查; {WATCH_LINE}-{PASS_LINE - 1} 有短板; <{WATCH_LINE} 不符合框架。")


if __name__ == "__main__":
    main()
