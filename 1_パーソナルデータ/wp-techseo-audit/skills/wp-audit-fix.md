# WordPress SEO修正適用

技術SEO監査で検出された問題を WordPress REST API 経由で修正適用します。

## 引数

$ARGUMENTS にクライアントIDを指定してください。（例: `naimono`）
オプションで修正プランファイルを指定: `naimono reports/naimono_fix_plan_20260227.json`

## 実行手順

あなたはテクニカルSEOの専門家です。安全性を最優先に修正を適用してください。

### Step 1: 修正プランの確認

修正プランファイルが指定されている場合はそれを読み込みます。
指定がない場合は、直近のクロール監査レポート（`reports/{client}_fix_plan_*.json`）を検索して最新のものを使用します。

修正プランの内容をユーザーに提示し、確認を得てからのみ実行します。

### Step 2: ドライラン実行

まずドライランで変更内容を確認します。

```bash
cd "C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit"
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/wp_meta_updater.py --client <client_id> --plan <plan_file>
```

ドライランの結果をユーザーに提示：
- 変更対象のページ数
- 各ページでの変更内容（before → after）
- リダイレクト作成予定

### Step 3: ユーザー確認

**重要**: 以下の情報を提示してユーザーの明示的な承認を得ること：

```
## 修正プラン確認

以下の変更を適用してよろしいですか？

| # | ページ | 変更内容 | Before | After |
|---|--------|---------|--------|-------|
| 1 | /article/123 | meta_title | 旧タイトル | 新タイトル |
| 2 | /article/456 | meta_description | 旧ディスクリプション | 新ディスクリプション |

リダイレクト作成: N件
ロールバックファイル: 自動生成されます

[y/n]
```

### Step 4: 修正適用

ユーザーの承認後に `--execute` フラグ付きで実行：

```bash
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/wp_meta_updater.py --client <client_id> --plan <plan_file> --execute
```

### Step 5: 適用結果の確認

- 各変更の成功/失敗を確認
- ロールバックファイルのパスを記録
- 変更ログをレポートに出力

### Step 6: レポート生成

```markdown
# 修正適用レポート

**クライアント**: [名前]
**適用日時**: [日時]
**修正プラン**: [ファイルパス]

## 適用結果

| # | ページ | フィールド | 結果 | Before | After |
|---|--------|----------|------|--------|-------|
| 1 | ... | ... | ✅ 成功 | ... | ... |

## ロールバック

問題が発生した場合のロールバック手順：
```bash
python wp_meta_updater.py --client <client_id> --plan <rollback_file> --execute
```

ロールバックファイル: [パス]

## 次のステップ

- インデックス確認: `/wp-audit-index $ARGUMENTS`
- パフォーマンス再測定: `/wp-audit-lighthouse $ARGUMENTS`
```

## 注意事項

- **ドライランなしでの実行は絶対に行わない**
- **ユーザーの明示的な承認なしに修正を適用しない**
- スラッグの変更は内部リンク破損リスクがあるため特に注意
- 大量の変更（50件以上）は分割して適用を推奨
- ロールバックファイルは必ず保存し、ユーザーに場所を伝える
