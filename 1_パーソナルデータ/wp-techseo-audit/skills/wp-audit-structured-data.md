# WordPress 構造化データ検証

WordPress サイトの構造化データ（JSON-LD / Microdata）を検証し、修正コードを生成します。

## 引数

$ARGUMENTS にクライアントIDを指定してください。（例: `naimono`）
オプションで対象URLを追加指定できます。

## 実行手順

あなたはテクニカルSEOの専門家です。以下の手順で構造化データ検証を実施してください。

### Step 1: 対象URL の決定

wp_reader.py でサイトのページ一覧を取得し、サンプルを選定します：
- トップページ
- 主要カテゴリページ（5ページ）
- 記事ページ（ランダム10ページ）
- 固定ページ（全ページ）

```bash
cd "C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit"
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/wp_reader.py --client $ARGUMENTS --action posts
```

### Step 2: 構造化データの抽出と検証

各URLの構造化データを検証します。

```bash
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/structured_data_validator.py <URL>
```

複数URLの場合はURLリストファイルを作成してバッチ実行：
```bash
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/structured_data_validator.py --batch urls.txt --output "./reports/"
```

### Step 3: 問題の分析

検出された問題を以下の観点で分析：

1. **必須フィールドの欠落**（重要度: HIGH）
   - Article: headline, author, datePublished, publisher, image
   - FAQPage: mainEntity, Question.name, acceptedAnswer.text
   - BreadcrumbList: itemListElement, position, name

2. **推奨フィールドの欠落**（重要度: MEDIUM）
   - dateModified, description, articleBody
   - Organization の logo, contactPoint

3. **ベストプラクティス違反**（重要度: LOW）
   - author が "admin" になっている
   - headline が110文字超
   - image の指定漏れ

### Step 4: 修正コード生成

問題のある構造化データに対して、修正済みの JSON-LD コードを生成します。
`--generate-fix` オプションで修正コードを取得：

```bash
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/structured_data_validator.py <URL> --generate-fix
```

### Step 5: レポート生成

```markdown
# 構造化データ検証レポート

**クライアント**: [名前]
**検証日時**: [日時]
**検証ページ数**: [N]

## サマリー

| 指標 | 値 |
|------|-----|
| 検証ページ数 | N |
| スキーマ検出ページ | N |
| スキーマ未設定ページ | N |
| エラー総数 | N |
| 警告総数 | N |

## 検出されたスキーマタイプ

| タイプ | 検出数 | エラー | 警告 |
|--------|--------|--------|------|
| Article | N | N | N |
| FAQPage | N | N | N |
| BreadcrumbList | N | N | N |

## 問題一覧（優先度順）

### HIGH: 必須フィールド欠落
...

### MEDIUM: 推奨フィールド欠落
...

## 修正コード

### [URL 1]
\```json
{ 修正済みJSON-LD }
\```

## 次のステップ

- 技術SEOクロール: `/wp-audit-crawl $ARGUMENTS`
- 修正適用: `/wp-audit-fix $ARGUMENTS`
```

レポートは `reports/{client}_structured_data_{date}.md` に保存。

## 注意事項

- WordPress のSEOプラグイン（Yoast / Rank Math）が生成する構造化データのパターンを理解した上で検証
- @graph 構造の中に複数のスキーマが含まれるケースに対応
- 修正コードはそのまま WordPress のカスタムHTMLブロックやテーマに貼り付けられる形式で出力
