# 📈 バフェット式バリュー投資（米国株）｜5か年財務基準 + PE/PB 分位を一括スクリーニング

**[中文](README.md) | [English](README.en.md) | [日本語](README.ja.md)**

作者：Serennity007（オリジナル）| License：MIT | データ：akshare（東方財富 米国株財務指標 / 新浪 米国株日足）

バフェットの財務基準で米国株をスクリーニングし、個別銘柄を深掘りします。5 か年連続の ROE、粗利率の安定性、負債比率、営業キャッシュフローの黒字継続、さらに現在の PE・PB が自社過去 5 年のどの分位にあるかを確認できます。既定のユニバースは同梱の NASDAQ-100 リスト（101 銘柄、出典と取得日付き）。任意のティッカーも指定可能です。

## クイックスタート

```bash
pip install akshare pandas

# 同梱ユニバースを一括採点（101 銘柄、各 3 回 API 呼び出し）
python scripts/screen.py --top 20 --out result.csv

# 自选リストを採点
python scripts/screen.py --tickers MSFT,COST,PEP,ADBE

# 個別銘柄の詳細分析（堀の人手チェックリスト付き）
python scripts/analyze.py --ticker MSFT
```

## 出力例（2026-10-12 実測、7 銘柄サンプル）

```
ticker  total  roe_score  gross_score  debt_score  fcf_score  valuation_score pe_pct pb_pct  data_years
  MSFT     89         30           20           8         20               11   0.37   0.22           5
  ADBE     88         30           20           3         20               15   0.01   0.01           5
  NVDA     83         30           10          15         20                8   0.26      —           5
  COST     70         30           10           3         20                7   0.45   0.40           5
```

```
=== ランキングから除外（指標が成立しない 3 銘柄）===
ticker  total  gross_score  fcf_score  valuation_score  debt_latest                 flag
  BKNG     48           20         20                8        119.1 权益≤0，ROE/负债率/PB 均不适用
  ORLY     44           20         20                4        104.6 权益≤0，ROE/负债率/PB 均不适用
  SBUX     40           20         20                0        125.3 权益≤0，ROE/负债率/PB 均不适用
```

（flag 列はスクリプト出力そのままの中国語。意味は「自己資本 ≤ 0 のため ROE・負債比率・PB いずれも適用不能」。）

判定ライン：**≥80 は堀の人手確認へ／60–79 は明確な弱点あり／<60 は本フレームに非該当**。完全なランキングは [docs/demo.md](docs/demo.md)。

## スクリーニング基準

| 項目 | 基準 | データフィールド |
|---|---|---|
| ROE | 5 か年連続 > 15% | `ROE_AVG` |
| 粗利率 | 平均 > 30% かつ 5 年の幅 < 5pp | `GROSS_PROFIT_RATIO` |
| 負債比率 | < 50%（金融は該当せず） | `DEBT_ASSET_RATIO` |
| フリーキャッシュフロー | 5 か年連続で黒字（営業CF + 固定資産購入） | キャッシュフロー計算書から2項目を取得 |
| バリュエーション | PE / PB が自社 5 年の低位 | 日足終値 × 年度 EPS / ROE で算出 |

配点は [references/scoring_rules.md](references/scoring_rules.md)、堀と資本配分の判断枠組みは [references/buffett_principles.md](references/buffett_principles.md) を参照。

## A 株版との意図的な違い（3 点）

1. **ユニバースは静的ファイル**。A 株版は沪深300 構成銘柄を実時間で取得できますが、米国全上場リストの API はネットワーク環境により到達不可の場合があるため、`data/universe_nasdaq100.json`（`source` / `as_of` / `fetched_at` 付き）を同梱しています。四半期ごとの構成変更は自分で更新するか、`--tickers` で上書きしてください。
2. **キャッシュフロー基準と歪み処理を米国株向けに再調整**：FCF に変更、負の自己資本は N/A、判定ラインは 80 に引き上げ。そのため**スコアは A 株版と直接比較できない**（`references/scoring_rules.md` 参照）。
3. **PE/PB 分位は近似値**。米国株には日次履歴バリュエーション API が無いため、日次 PE = 終値 ÷ 当年度基本 EPS、日 PB = PE × 当年度 ROE（P/B = P/E × E/B の恒等式）で構築します。年度内で EPS・ROE 一定、開示遅延なしと仮定する近似なので、「自社履歴で割高か割安か」の判断に限定してください。

## 同梱ファイル

- `SKILL.md` — エージェント用スキル定義
- `scripts/screen.py` — ユニバース採点（`--universe` / `--tickers` / `--top` / `--out` / `--sleep`）
- `scripts/analyze.py` — 個別銘柄レポート（`--ticker` / `--years` / `--out`）
- `data/universe_nasdaq100.json` — 既定ユニバースと出典
- `references/` — 配点ルールと原則
- `docs/demo.md` — 実測の完全ランキング

## データ上の制約

- 一部の企業は東方財富の米国株財務 API にカバレッジがありません（スクリプトは報告して継続します。保険業が典型）。
- 複数議決権やドット入りティッカーは表記が特殊：バークシャー・ハサウェイは `BRK.B`。
- 決算月末が銘柄ごとに異なる（マイクロソフト 6 月、エヌビディア 1 月、アップル 9 月）。自社履歴との比較のみで、業種横断の比較は行いません。

## 免責事項

学習・研究目的のみであり、投資助言ではありません。財務データは第三者 API 由来で、欠損・遅延・再修正の可能性があります。判断の前に SEC EDGAR の 10-K / 10-Q 原典で確認してください。
