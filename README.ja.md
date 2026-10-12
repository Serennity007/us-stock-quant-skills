# us-stock-quant-skills

**[中文](README.md) | [English](README.en.md) | [日本語](README.ja.md)**

![License](https://img.shields.io/badge/License-MIT-blue)
![Data](https://img.shields.io/badge/data-akshare-lightgrey)

米国株クオンツ／銘柄選定 AI スキルのコレクション。再現可能なスクリーニングと採点はスクリプトに、判断枠組みはドキュメントに置き、Claude Code や汎用 Agent Skills ディレクトリから読み込めます。データはすべて公開インターフェースで、API key 不要。

- **免責事項**：学習・研究目的のみであり、投資助言ではありません。結論は第三者の公開データに依存し、欠損・遅延・再修正の可能性があります。判断の前に SEC EDGAR の 10-K / 10-Q 原典を確認してください。
- **収録開始日**：2026-10-11。

## 使い方

必要なスキルディレクトリを自分のスキルフォルダにコピーするだけです：

```bash
# Claude Code
cp -r buffett-value-investing-us ~/.claude/skills/

# 汎用 agents skills ディレクトリ
cp -r buffett-value-investing-us ~/.agents/skills/
```

依存：`pip install akshare pandas`（Python ≥ 3.9、API key 不要）。

## 収録スキル

| スキル | 内容 | データ源 |
|---|---|---|
| [buffett-value-investing-us](buffett-value-investing-us) | バフェット式バリュー投資：5 か年連続の ROE・粗利率・負債比率・営業 CF 基準＋自社履歴に対する PE/PB 分位。ユニバース採点と個別銘柄深掘り | akshare（東方財富 米国株財務・CF 計算書／新浪 米国株日足） |

各スキルの構成は共通：

```
<skill>/
├── SKILL.md              # スキル定義（エージェント読み込み口）
├── README.md/.en/.ja     # 三言語ドキュメント
├── scripts/              # 実行可能スクリプト
├── references/           # 配点ルールと判断枠組み
├── data/                 # 出典・取得日付きの静的データ
└── docs/demo.md          # 実測出力
```

## データと出典

- **相場・財務**：[akshare](https://github.com/akfamily/akshare) 経由の公開 API（東方財富、新浪財経）。すべての呼び出しで指数バックオフ再試行、1 銘柄の失敗で全体を中断せず、最後に失敗一覧をまとめます。
- **ユニバース**：`buffett-value-investing-us/data/universe_nasdaq100.json` は Nasdaq 公式 `api.nasdaq.com/api/quote/list-type/nasdaq100` 由来。構成 **2026-10-09 時点**、取得 **2026-10-11**。構成銘柄は四半期に見直され、本リポジトリは自動同期しません。`--tickers` で上書き可能です。
- **既知の API 制約**：A 株版にある「全構成銘柄一覧」および「日次履歴バリュエーション」の API が米国株には存在しません。そのためユニバースは静的ファイル、PE/PB 分位は日足終値と年度 EPS/ROE から再構成した近似値です（各スキル文書に明記）。

## ロードマップ

当面は旗艦スキル 1 本で、データ層と採点基準を固めます。以降同じテンプレートで米国株版を追加予定：モメンタム／相対力（CANSLIM）、市場サイクル温度計、マクロダッシュボード。名前はすべて `-us` 接尾辞を付け、A 株スキルとの衝突を防ぎます。

## License

[MIT](LICENSE)、© 2026 Serennity007。akshare および上流データ源のライセンスは各自の条件に従います。
