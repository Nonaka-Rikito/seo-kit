# ナイモノ（jo-katsu.com）SEO修正 実行プラン

**作成日**: 2026-02-27
**監査レポート**: `naimono_full_audit_20260227.md`
**修正プラン**: `naimono_fix_plan_20260227.json`

---

## 全体サマリー

| 分類 | 件数 | 対応方法 |
|------|------|---------|
| API自動修正（`wp_meta_updater.py`） | 4件 | Phase 1-2 で実行 |
| クライアント確認後に判断 | 1件 | Phase 0 で確認 |
| 手動対応（開発者向け指示書） | 8件 | Phase 3 で指示書作成 |

---

## Phase 0: 事前準備（実行前に必須）

### 0-1. post_id マッピングテーブルの作成

クロールデータに `post_id` が含まれていないため、WP REST API で URL → post_id の対応表を取得する。

```bash
PYTHON="C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python"
cd "C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit"

$PYTHON scripts/wp_reader.py --client naimono --action pages
$PYTHON scripts/wp_reader.py --client naimono --action posts
```

取得後、以下の対象ページの post_id を特定する:
- `/faqs/faq1` 〜 `/faq6`（6件）
- `/gallerys/item_house`, `/item_ticket`, `/item_adviser`（3件）
- `/news`, `/news/20190925`（2件）
- `/online`, `/business`, `/biz`（3件）
- `/campus_list`, `/es-info`, `/contact`（3件）
- `/house`, `/ticket`, `/event`（3件）
- `/story/page/2`（1件）

### 0-2. クライアント確認事項（ナイモノへの質問）

以下5ページの **noindex が意図的かどうか** を確認する必要がある:

| # | URL | 現在の状態 | 質問 |
|---|-----|-----------|------|
| 1 | `/news` | noindex | ニュース一覧はインデックスさせたいか？ |
| 2 | `/online` | noindex | オンラインページは現在有効なコンテンツか？ |
| 3 | `/business` | noindex | ビジネスページは現在有効か？ |
| 4 | `/biz` | noindex | `/business` との関係は？片方はリダイレクトすべき？ |
| 5 | `/news/20190925` | noindex | 2019年のニュースページは残す必要があるか？ |

**確認方法**: Slack `pj_cw_na_media` チャンネルで清宮さんまたは担当者に確認

**残り10件の判定**:
- `/faqs/faq1〜6`（6件）: 旧URL構造の残骸 → **noindex維持が妥当**（canonical不整合のみ修正）
- `/gallerys/item_*`（3件）: `/house` `/ticket` `/adviser` と重複 → **noindex維持が妥当**
- `/story/page/2`: ページネーション2ページ目 → **noindex維持が妥当**（Yoastデフォルト挙動）

---

## Phase 1: 安全な自動修正（クライアント確認不要）

### 1-1. canonical 不整合修正（FIX-005）— 10件

**リスク: 低** — 存在しない旧URLから正しい自己参照URLへの変更。noindexページなのでインデックスへの悪影響なし。

| # | URL | 現在の canonical（誤） | 修正後の canonical（正） |
|---|-----|----------------------|----------------------|
| 1 | `/faqs/faq1` | `https://jo-katsu.com/faq/faqs/faq1/` | `https://jo-katsu.com/faqs/faq1/` |
| 2 | `/faqs/faq2` | `https://jo-katsu.com/faq/faqs/faq2/` | `https://jo-katsu.com/faqs/faq2/` |
| 3 | `/faqs/faq3` | `https://jo-katsu.com/faq/faqs/faq3/` | `https://jo-katsu.com/faqs/faq3/` |
| 4 | `/faqs/faq4` | `https://jo-katsu.com/faq/faqs/faq4/` | `https://jo-katsu.com/faqs/faq4/` |
| 5 | `/faqs/faq5` | `https://jo-katsu.com/faq/faqs/faq5/` | `https://jo-katsu.com/faqs/faq5/` |
| 6 | `/faqs/faq6` | `https://jo-katsu.com/faq/faqs/faq6/` | `https://jo-katsu.com/faqs/faq6/` |
| 7 | `/gallerys/item_house` | `https://jo-katsu.com/gallery/gallerys/item_house/` | `https://jo-katsu.com/gallerys/item_house/` |
| 8 | `/gallerys/item_ticket` | `https://jo-katsu.com/gallery/gallerys/item_ticket/` | `https://jo-katsu.com/gallerys/item_ticket/` |
| 9 | `/gallerys/item_adviser` | `https://jo-katsu.com/gallery/gallerys/item_adviser/` | `https://jo-katsu.com/gallerys/item_adviser/` |
| 10 | `/story/page/2` | `https://jo-katsu.com/story/` | `https://jo-katsu.com/story/page/2/` |

**実行手順**:
1. post_id 取得後、実行用 JSON を生成
2. ドライラン → before/after 確認
3. 承認後に `--execute` で適用

### 1-2. 重複タイトル修正（FIX-007）— 4グループ・4ページ

**リスク: 低〜中** — noindex/旧URLページ側のタイトルを変更するだけ。検索結果に影響するページは変更しない。

| グループ | 変更対象URL | 現在のタイトル | 修正案 |
|---------|-----------|-------------|-------|
| G1 | `/news/20190925` | ニュース \| …ジョーカツ | `2019年9月25日のニュース \| ジョーカツ` |
| G2 | `/gallerys/item_house` | ジョーカツハウス \| …ジョーカツ | `ジョーカツハウス（ギャラリー） \| ジョーカツ` |
| G3 | `/gallerys/item_ticket` | ジョーカツ切符 \| …ジョーカツ | `ジョーカツ切符（ギャラリー） \| ジョーカツ` |
| G4 | `/faqs/faq4` | ジョーカツイベント \| …ジョーカツ | `よくある質問4 \| ジョーカツ` |

**注意**: G1〜G4 は全て noindex ページのため、SEOへの実質的影響はほぼゼロ。ただし正確なタイトルにしておくことで管理上の混乱を防ぐ。

---

## Phase 2: クライアント確認後の自動修正

### 2-1. noindex 解除（FIX-004）— 最大5件

Phase 0-2 のクライアント確認結果に応じて実行。

**確認結果の想定パターン**:

| パターン | 対応 |
|---------|------|
| `/news` をインデックスさせたい | Yoast robots meta を `index` に変更 |
| `/online` は廃止コンテンツ | noindex維持 or 301リダイレクト |
| `/business` と `/biz` が重複 | 片方を301リダイレクト、もう片方をインデックス |

### 2-2. メタディスクリプション追加（FIX-009）— 優先10件

**リスク: 低** — 未設定箇所への追加のみ。既存のものを上書きしない。

| 優先 | URL | 提案するメタディスクリプション |
|-----|-----|--------------------------|
| 1 | `/campus_list` | ジョーカツの就活ハンドブック記事一覧。自己分析、ES対策、面接対策、企業研究など就活に役立つ情報を掲載しています。 |
| 2 | `/es-info` | 企業別のエントリーシート（ES）情報をまとめたページ。各企業の選考ポイントや通過ESの傾向を確認できます。 |
| 3 | `/contact` | ジョーカツへのお問い合わせページ。サービスに関するご質問やご相談はこちらからお気軽にどうぞ。 |
| 4〜10 | `/es-info/*` | （各企業名）のエントリーシート情報 \| 選考ポイント・ES通過のコツをジョーカツが解説。 |

**注意**: `/es-info` 配下は数十ページあるため、Yoastの**カスタム投稿タイプテンプレート**で `%%title%% のエントリーシート情報。選考のポイントやES通過のコツをジョーカツが解説します。` のようなテンプレートを設定する方が効率的。これは `wp_meta_updater.py` では対応できず、**WordPress管理画面での手動設定が必要**。

---

## Phase 3: 手動対応（開発者・クライアント向け指示書）

以下はWP REST API経由では対応できない項目。ナイモノの開発担当者への指示書として提出する。

### 3-1. サーバーパフォーマンス改善（FIX-001 / CRITICAL）

**対象**: 全ページ（TTFB平均 1,271ms 遅延）
**SLA**: 1週間

| # | タスク | 担当 | 備考 |
|---|-------|------|------|
| 1 | Redis Object Cache プラグイン導入 | サーバー管理者 | `WP Redis` or `Redis Object Cache` プラグイン |
| 2 | PHP OPcache 有効化確認 | サーバー管理者 | `php.ini` で `opcache.enable=1` |
| 3 | CDN（CloudFlare）導入検討 | クライアント判断 | 無料プランでも効果あり |
| 4 | campus ページの DB クエリプロファイリング | 開発者 | `Query Monitor` プラグインで調査 |

### 3-2. リダイレクトチェーン排除（FIX-002 / CRITICAL）

**対象**: campus系10ページ（モバイルLCP 30秒超の一因）
**SLA**: 1週間

| # | タスク |
|---|-------|
| 1 | campus ページへの内部リンクで trailing slash なしURL（`/campus/37260`）を使っている箇所を特定 |
| 2 | 全内部リンクを正規URL（`/campus/37260/`）に書き換え |
| 3 | WordPress Permalink 設定で trailing slash の挙動を確認 |

### 3-3. トップページ CLS 修正（FIX-003 / CRITICAL）

**対象**: `/`（CLS 0.282 → 目標 0.1未満）
**SLA**: 1週間

| # | タスク |
|---|-------|
| 1 | ヒーロー画像・バナーに `width` / `height` 属性を追加 |
| 2 | スライダー・カルーセルにプレースホルダースペースを CSS で確保 |
| 3 | Web フォントに `font-display: swap` + `<link rel="preload">` 設定 |

### 3-4. GSC サイトマップ再提出（FIX-006 / HIGH）

**対象**: campus/sitemap.xml（1年7ヶ月間ダウンロードされていない）
**SLA**: 即日

| # | タスク | 担当 |
|---|-------|------|
| 1 | `https://jo-katsu.com/campus/sitemap.xml` にブラウザでアクセスし存在確認 | malna |
| 2 | Yoast SEO → サイトマップ → 再生成 | malna or クライアント |
| 3 | GSC で既存サイトマップを削除 → 再提出 | malna（GSCアクセスあれば） |

### 3-5. H1 タグ重複のテーマ修正（FIX-008 / MEDIUM）

**対象**: 92ページ（H1が2個存在）+ 8ページ（H1なし）
**SLA**: 1ヶ月

| # | タスク |
|---|-------|
| 1 | テーマの `header.php` / `single.php` / `page.php` でH1レンダリング箇所を確認 |
| 2 | サイトタイトル（ロゴ部分）の `<h1>` を `<div>` or `<p>` に変更 |
| 3 | `/`, `/campus/`, `/campus_list` にコンテンツH1を追加 |

### 3-6. Article/BlogPosting スキーマ実装（FIX-010 / MEDIUM）

**対象**: `/campus/` 配下の全記事
**SLA**: 1ヶ月

| # | タスク |
|---|-------|
| 1 | Yoast SEO → 検索の見え方 → コンテンツタイプ → campus の Article スキーマを有効化 |
| 2 | 必須フィールド確認: headline, author, datePublished, image, publisher |

### 3-7. Organization スキーマ補完（FIX-011 / MEDIUM）

| # | タスク |
|---|-------|
| 1 | Yoast SEO → 検索の見え方 → 組織 → logo / contactPoint / address を追加 |

### 3-8. 未使用 CSS/JS 削減（FIX-013 / MEDIUM）

| # | タスク |
|---|-------|
| 1 | `Asset CleanUp` or `Perfmatters` プラグインで投稿タイプ別にCSS/JS読み込み制御 |
| 2 | gzip/brotli 圧縮の有効化確認 |

---

## 実行スケジュール

```
Week 0（今日）
  └── Phase 0: post_id取得 + クライアントへ確認連絡

Week 1
  ├── Phase 1-1: canonical修正（10件・自動）
  ├── Phase 1-2: 重複タイトル修正（4件・自動）
  ├── Phase 3-1: サーバーパフォーマンス指示書提出
  ├── Phase 3-2: リダイレクトチェーン指示書提出
  ├── Phase 3-3: CLS修正指示書提出
  └── Phase 3-4: GSCサイトマップ再提出（即日対応可）

Week 2
  ├── Phase 2-1: noindex解除（確認結果に応じて）
  ├── Phase 2-2: メタディスクリプション追加（優先10件）
  └── Phase 3-5〜3-8: 中期修正の指示書提出

Week 3-4
  └── 効果測定（/wp-audit-lighthouse + /wp-audit-index で再監査）
```

---

## 実行用 JSON テンプレート（Phase 0 完了後に post_id を埋める）

```json
{
  "fixes": [
    {
      "post_id": "<<要取得>>",
      "post_type": "pages",
      "updates": {
        "canonical": "https://jo-katsu.com/faqs/faq1/"
      }
    }
  ]
}
```

Phase 0 の post_id 取得完了後、このテンプレートに値を埋めて `wp_meta_updater.py --plan` で実行する。
