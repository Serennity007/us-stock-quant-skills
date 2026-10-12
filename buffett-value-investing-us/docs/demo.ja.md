# 実測ランキング：NASDAQ-100 全銘柄スクリーニング

- 実行日：2026-10-11
- コマンド：`python scripts/screen.py --top 25 --out screen_result.csv`
- 結果：**101 銘柄すべて採点成功、失敗 0**（各呼び出しは指数バックオフで再試行。前回は一部コードが一時的にレート制限されたが再実行で回復）
- 分布：≥70 → **46 銘柄**｜50–69 → **33 銘柄**｜<50 → **22 銘柄**

## 上位 25 銘柄

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

読み方：5 項目すべてをクリアする CPRT（コンテナリース、スイッチングコスト型）がこの手法の教科書的な狙い目。FAST や ODFL は「事業品質は合格、価格が不合格」。ADBE・INTU・CMCSA はバリュエーション分位が 0.05 以下なのに ROE と粗利率が健全という、この手法が探す組み合わせそのもの。

## 下位 8 銘柄

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

下位は二群に分かれる。**連続した利益記録のない新規上場／高成長株**（RKLB、NBIS、CRWV、ARM、ALAB、SNDK）と、**構造的に高レバレッジで ROE が低い公益事業など**（XEL、CEG）。どちらも本フレームの対象外で、「不適合」であって「不当な安売り」ではない。

## 今回の実行で露呈した実上の限界（表と必ず一緒に読むこと）

1. **7 銘柄は会計年度が 5 年未満**：ARM、FER、ALAB、SNDK、HONA、SPCX、CRWV。SNDK は 2025 年 2 月のウエスタン・デジタルからのスピンオフ後に単独報告が始まったため 1 年分で、得点上限が下がり、履歴満了銘柄と同列に順位付けできない。スクリプトは実行末尾でこれらを個別に列挙する。
2. **4 銘柄は PE 分位なし**：HONA、SPCX、CRWV、RKLB — 直近年度の基本 EPS が正でないため PE が定義できない。
3. **5 銘柄は PB 分位なし**：上記 4 つに加え **SBUX**。スターバックスはこのアルゴリズムの構造的盲点で、長年の自社株買いにより株主資本がゼロ以下に近く、ROE が負または無意味になる。本スキルの PB は恒等式 `PB = PE × ROE` から構成しているため、資本が負では成立しない。**結論：自社株買いを資本配分の主手段とする企業では、必ず貸借対照表の原値に戻り、この分位を使わないこと。**
4. **GOOG と GOOGL が別枠で並ぶ**：同一会社の 2 銘柄なのでランキングは重複計上。人手確認時に統合すること。
5. **`pe_pct = 1.00`（TER）は実数値**で、エラーではない：現在の PE が自社 5 年レンジの上限にあることを意味する。

## 再現方法

```bash
pip install akshare pandas
git clone https://github.com/Serennity007/us-stock-quant-skills.git
cd us-stock-quant-skills/buffett-value-investing-us
python scripts/screen.py --top 25 --out screen_result.csv
python scripts/analyze.py --ticker CPRT
```

ランキングは相場と開示で動く。上の表は 2026-10-11 の一時点の記録であり、投資助言ではない。
