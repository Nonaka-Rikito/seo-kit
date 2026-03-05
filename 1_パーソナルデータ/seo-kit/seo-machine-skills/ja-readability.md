# 日本語可読性分析スキル

## 概要
日本語コンテンツの可読性をJanome形態素解析で定量的にスコアリングする。

## 使用方法
ユーザーが以下のいずれかを指示した場合にこのスキルを実行する：
- 「可読性を分析して」「読みやすさチェック」「可読性スコア」
- 日本語コンテンツの品質評価を求められた場合

## 実行手順

### 1. 対象コンテンツの取得
- URLが指定された場合：WebFetchでコンテンツを取得
- ファイルが指定された場合：Readで読み込み
- テキストが直接渡された場合：そのまま使用

### 2. 可読性分析の実行
```python
import sys
sys.path.insert(0, r'c:\Users\rikit\Projects\seo-machine')
from data_sources.japanese.readability_scorer_ja import ReadabilityScorerJa

scorer = ReadabilityScorerJa()
result = scorer.analyze(content)
```

### 3. 結果の解釈と報告

返却値から以下を報告する：
- `overall_score`: 総合スコア（0-100）
- `grade`: A（優秀）〜 F（要大幅改善）
- `character_metrics.kanji_ratio`: 漢字比率（目標: 20-35%）
- `character_metrics.hiragana_ratio`: ひらがな比率（目標: 35-55%）
- `sentence_metrics.avg_length`: 平均文長（目標: 40-80文字）
- `sentence_metrics.very_long_sentences`: 150文字超の文の数
- `structure_metrics`: 見出し・段落構成
- `recommendations`: 改善提案リスト

### 4. レポート形式

```
## 可読性分析レポート

| 指標 | 値 | 判定 |
|------|-----|------|
| 総合スコア | XX/100 | グレード |
| 漢字比率 | XX% | ○/△/× |
| ひらがな比率 | XX% | ○/△/× |
| 平均文長 | XX文字 | ○/△/× |
| 長文数 | X文 | ○/△/× |

### 改善提案
- ...
```

## 判定基準
- **A（90-100）**: SEOに最適な可読性
- **B（80-89）**: 良好、微調整で完璧に
- **C（70-79）**: 標準的、改善余地あり
- **D（60-69）**: 改善が必要
- **F（0-59）**: 大幅な改善が必要

## 注意事項
- 英語テキストには使用しないこと（textstatを使用）
- Markdownの見出し・リンクは自動除去される
- スコアはjo-katsu.comのブランドボイス（`context/naimono/brand-voice.md`）と照合して解釈すること
