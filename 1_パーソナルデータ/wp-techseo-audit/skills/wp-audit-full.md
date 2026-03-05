# WordPress 総合テクニカルSEO監査

WordPress サイトの技術SEOを MECE に総合監査するオーケストレータースキルです。
5つの個別監査ステップを順次実行し、統合レポートを生成します。

## 引数

$ARGUMENTS にクライアントIDを指定してください。（例: `naimono`）

## 実行手順

あなたはテクニカルSEOの専門家です。以下の5ステップで総合監査を実施してください。

### 全体フロー

```
Step 1: パフォーマンス & CWV（/wp-audit-lighthouse）
    ↓
Step 2: 構造化データ検証（/wp-audit-structured-data）
    ↓
Step 3: 技術SEOクロール（/wp-audit-crawl）
    ↓
Step 4: 修正適用（/wp-audit-fix）← ユーザー確認後のみ
    ↓
Step 5: インデックス確認（/wp-audit-index）
```

### Step 1: パフォーマンス監査

`/wp-audit-lighthouse $ARGUMENTS` のワークフローを実行します。

主要ページ（トップ + カテゴリ上位5 + 人気記事上位5）に対して Lighthouse 監査を実施し、CWV と パフォーマンススコアを取得します。

### Step 2: 構造化データ検証

`/wp-audit-structured-data $ARGUMENTS` のワークフローを実行します。

サンプルページの JSON-LD / Microdata を検証し、エラーと修正コードを生成します。

### Step 3: 技術SEOクロール

`/wp-audit-crawl $ARGUMENTS` のワークフローを実行します。

サイト全体（またはサンプル）をクロールし、メタ情報・サイト構造・コンテンツ・リダイレクトの問題を検出します。

### Step 4: 修正計画の提示

Step 1-3 の結果を統合し、修正計画を作成します。

**注意**: 実際の修正適用（`/wp-audit-fix`）はユーザーの明示的な指示があった場合のみ実行します。このステップでは修正計画の提示のみ行います。

### Step 5: インデックス確認

`/wp-audit-index $ARGUMENTS` のワークフローを実行します。

GSC でインデックス状況を確認し、問題ページを特定します。

### 統合レポート生成

全ステップの結果を統合した総合レポートを生成します。

```markdown
# WordPress テクニカルSEO 総合監査レポート

**クライアント**: [名前]
**対象サイト**: [URL]
**監査日時**: [日時]
**監査ステップ**: 全5ステップ完了

---

## エグゼクティブサマリー

[3-5行で監査結果の概要。最も重要な発見事項と推奨アクションを記述]

## スコアカード

| カテゴリ | スコア | 検出問題数 | 最高重要度 |
|---------|--------|-----------|-----------|
| パフォーマンス (PERF) | XX/100 | N | CRITICAL/HIGH/MEDIUM/LOW |
| メタ情報 (META) | — | N | ... |
| サイト構造 (STRC) | — | N | ... |
| 構造化データ (SCHM) | — | N | ... |
| インデックス (INDX) | — | N | ... |
| コンテンツ (CONT) | — | N | ... |
| リダイレクト (RDIR) | — | N | ... |
| モバイル (MOBL) | — | N | ... |

## 問題サマリー（重要度別）

| 重要度 | 件数 | SLA |
|--------|------|-----|
| CRITICAL | N | 即日 |
| HIGH | N | 1週間 |
| MEDIUM | N | 1ヶ月 |
| LOW | N | バックログ |

## CRITICAL 問題（即日対応）

[問題の詳細と具体的な対応手順]

## HIGH 問題（1週間以内）

[問題の詳細と具体的な対応手順]

## 修正ロードマップ

### Week 1: 緊急対応
- [ ] CRITICAL 問題の修正
- [ ] ...

### Week 2-4: 重要対応
- [ ] HIGH 問題の修正
- [ ] ...

### Month 2+: 継続改善
- [ ] MEDIUM/LOW 問題の修正
- [ ] ...

## 個別レポートへのリンク

- Lighthouse: `reports/{client}_lighthouse_{date}.md`
- 構造化データ: `reports/{client}_structured_data_{date}.md`
- クロール: `reports/{client}_crawl_{date}.md`
- インデックス: `reports/{client}_index_{date}.md`

## 次のアクション

1. CRITICAL問題の即座の修正: `/wp-audit-fix $ARGUMENTS`
2. 修正後の再監査（1週間後推奨）
3. 月次定期監査の設定
```

レポートは `reports/{client}_full_audit_{date}.md` に保存。
修正プランは `reports/{client}_fix_plan_{date}.json` に保存。

## 注意事項

- 各ステップは独立しても実行可能。途中で中断した場合は個別スキルで再開できる
- 大規模サイトの場合、全ステップ完了に30分以上かかることがある
- Step 4（修正適用）は必ずユーザーの明示的な承認を得ること
- レポートは全てマークダウン形式でファイル保存する
