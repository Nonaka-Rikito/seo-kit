# WordPress 技術SEOクロール監査

WordPress サイトを軽量クロールし、メタ情報・サイト構造・内部リンク・コンテンツの技術的問題を検出します。

## 引数

$ARGUMENTS にクライアントIDを指定してください。（例: `naimono`）
オプション: `--max-pages 50` でクロール上限を指定。

## 実行手順

あなたはテクニカルSEOの専門家です。以下の手順で技術SEOクロール監査を実施してください。

### Step 1: クライアント設定の確認

`config/clients.json` を読み込み、対象サイトの設定を確認します。
`defaults` セクションからサンプリング設定も確認します。

### Step 2: サイトクロール実行

```bash
cd "C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit"
"C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python" scripts/site_crawler.py <site_url> --max-pages <max_pages> --output "./reports/" --delay <crawl_delay>
```

クロール中の進捗を確認し、完了まで待機します。

### Step 3: 問題の分析

クロール結果のJSONを読み込み、以下のカテゴリで問題を分析します：

| コード | カテゴリ | 検出内容 |
|--------|---------|---------|
| META | メタ情報 | title/description の欠落・重複・長短、canonical 問題 |
| STRC | サイト構造 | H1の欠落・複数、見出し階層スキップ、孤立ページ |
| CONT | コンテンツ | 薄いコンテンツ、タイトル重複、alt欠損画像 |
| RDIR | リダイレクト | チェーン、404、ループ |
| INDX | インデックス | 不適切なnoindex、robots ブロック |

### Step 4: 内部リンクグラフ分析

クロール結果から内部リンクグラフを分析：
- 孤立ページの特定
- リンク集中ページの確認
- クリック深度の分布
- 1ページあたりの平均内部リンク数

### Step 5: Ahrefs データとの照合（任意）

Ahrefs MCP が利用可能な場合、外部指標と照合：
- 外部被リンク数とページ重要度の相関
- トラフィック上位ページの技術的問題
- 競合と比較した構造上の差異

### Step 6: レポート生成

```markdown
# 技術SEOクロール監査レポート

**クライアント**: [名前]
**対象サイト**: [URL]
**クロール日時**: [日時]
**クロールページ数**: [N] / [全ページ数]

## サマリー

| 指標 | 値 |
|------|-----|
| クロールページ数 | N |
| 内部リンク総数 | N |
| 外部リンク総数 | N |
| 平均レスポンスタイム | Xms |
| 問題のあるページ数 | N |

## 問題分布

| カテゴリ | CRITICAL | HIGH | MEDIUM | LOW | 合計 |
|---------|----------|------|--------|-----|------|
| META | N | N | N | N | N |
| STRC | N | N | N | N | N |
| CONT | N | N | N | N | N |
| RDIR | N | N | N | N | N |
| INDX | N | N | N | N | N |

## CRITICAL 問題

...

## HIGH 問題

...

## 内部リンクグラフ分析

- 孤立ページ: N件
- 最大クリック深度: N
- 深度分布: {1: N, 2: N, 3: N, ...}
- 被リンク数トップ10: [表]

## 修正計画

問題を `templates/fix-plan.md` の形式でまとめ、`/wp-audit-fix` で適用可能な JSON 修正プランも生成します。

## 次のステップ

- 修正適用: `/wp-audit-fix $ARGUMENTS`
- インデックス確認: `/wp-audit-index $ARGUMENTS`
```

レポートは `reports/{client}_crawl_{date}.md` に保存。
修正プランは `reports/{client}_fix_plan_{date}.json` に保存。

## 注意事項

- 大規模サイト（500ページ以上）ではサンプリングが自動適用される
- robots.txt を尊重してクロールする
- WordPress 管理画面やログインページはクロール対象外
- 日本語コンテンツの文字数カウントに対応
