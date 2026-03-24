# 日本語キーワード密度分析スキル

## 概要
Janome形態素解析を用いた日本語キーワード密度・配置・共起語の定量分析。

## 使用方法
ユーザーが以下のいずれかを指示した場合にこのスキルを実行する：
- 「キーワード密度を分析して」「キーワード配置チェック」
- 「このキーワードは適切に使われている？」
- コンテンツのSEO最適化評価を求められた場合

## 実行手順

### 1. 入力の準備
- **対象コンテンツ**: URL、ファイルパス、または直接テキスト
- **主キーワード**: 1つ（必須）
- **副キーワード**: 0〜5つ（任意）
- **目標密度**: デフォルト1.5%（変更可能）

### 2. キーワード分析の実行
```python
import sys
sys.path.insert(0, r'c:\Users\your-user\Projects\seo-machine')
from data_sources.japanese.keyword_analyzer_ja import KeywordAnalyzerJa

analyzer = KeywordAnalyzerJa()
result = analyzer.analyze(
    content,
    primary_keyword='メインキーワード',
    secondary_keywords=['サブ1', 'サブ2'],
    target_density=1.5,
)
```

### 3. 結果の解釈と報告

返却値から以下を報告する：

#### 主キーワード分析
- `primary_keyword.count`: 出現回数
- `primary_keyword.density`: 密度（%）
- `primary_keyword.density_status`: optimal / too_low / too_high / slightly_low / slightly_high
- `primary_keyword.critical_placements`: 重要位置の配置チェック
  - `in_first_200_chars`: 冒頭200文字内
  - `in_h1`: H1見出し内
  - `in_conclusion`: まとめ部分
  - `in_h2`: H2見出しでの使用率

#### 副キーワード分析
- 各副キーワードの出現回数と密度

#### キーワード品質
- `keyword_stuffing.risk_level`: none / medium / high
- `cooccurrence_terms`: 共起語リスト（上位15語）
- `related_terms`: 関連語リスト（上位20語）

### 4. レポート形式

```
## キーワード密度分析レポート

### 主キーワード「○○」
| 指標 | 値 | 判定 |
|------|-----|------|
| 出現回数 | X回 | - |
| 密度 | X.XX% | 目標: 1.0-2.0% |
| 冒頭配置 | ○/× | - |
| H1配置 | ○/× | - |
| H2配置 | X/Y見出し | - |
| まとめ配置 | ○/× | - |

### 副キーワード
| キーワード | 回数 | 密度 | 目標 |
|-----------|------|------|------|
| ○○ | X | X.XX% | 0.3-0.8% |

### 詰め込みリスク: ○○

### 共起語（活用候補）
○○, ○○, ○○ ...

### 改善提案
- ...
```

## 目標値（example-media.com基準）
- 主キーワード密度: **1.0〜2.0%**（`context/example-client/seo-guidelines.md`準拠）
- 副キーワード密度: **0.3〜0.8%**
- 詰め込み警告: 3.0%超
- H2見出し内のキーワード使用: 50%以上推奨

## 注意事項
- 形態素解析ベースのため、「就職活動」と「就活」は別キーワードとしてカウントされる
- 共起語はLSIキーワード候補として活用可能
- 密度は内容語（名詞・動詞・形容詞・副詞）ベースで計算される
