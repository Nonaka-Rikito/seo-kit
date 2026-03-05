# ナイモノ テクニカルSEO監査 — セッション引き継ぎ

**最終更新**: 2026-02-27 18:00
**次回セッションで「このファイルを読んで続きをやって」と伝えればOK**

---

## 今回のセッションで完了したこと

### 1. テクニカルSEO総合監査（/wp-audit-full naimono）

jo-katsu.com に対して全5ステップの技術SEO監査を実行した。

| ステップ | 内容 | 結果 |
|---------|------|------|
| Step 1 | Lighthouse パフォーマンス監査（mobile + desktop × 10ページ） | モバイル平均PSI 38.3（壊滅的） |
| Step 2 | 構造化データ検証 | エラー0件、警告42件 |
| Step 3 | サイトクロール（100ページ） | 全100ページに問題あり、計289件 |
| Step 4 | 修正プラン生成（13項目） | CRITICAL 3件、HIGH 4件、MEDIUM 6件 |
| Step 5 | GSCインデックス確認 | サイトマップ1年7ヶ月未ダウンロード |

### 2. 修正プランの実行可能性分析

修正プラン13件を精査し、以下を明らかにした:

- **API自動修正可能**: 4件（canonical修正、タイトル重複修正、メタディスクリプション追加、noindex解除）
- **手動対応が必要**: 9件（サーバー設定、テーマ修正、プラグイン導入、GSC操作等）
- **クライアント確認が必要**: noindex 5ページの意図確認

### 3. 実行プラン作成

4フェーズの段階的実行プランを作成した。

---

## 生成済みファイル一覧

全て `1_パーソナルデータ/wp-techseo-audit/reports/` に格納:

| ファイル | 内容 |
|---------|------|
| `naimono_full_audit_20260227.md` | 総合監査レポート（日本語、289件の問題を網羅） |
| `naimono_fix_plan_20260227.json` | 修正プラン（戦略レベル、13項目） |
| `naimono_fix_execution_plan_20260227.md` | **実行プラン（Phase 0〜3の詳細手順）** |
| `naimono_target_urls.txt` | Lighthouse対象URL一覧（10ページ） |
| `jo-katsu_com_crawl_20260227_170416.json` | クロール結果（100ページ分の生データ） |
| `jo-katsu.com_*_mobile_*.json` | Lighthouseモバイル結果（10ページ分） |
| `jo-katsu.com_*_desktop_*.json` | Lighthouseデスクトップ結果（10ページ分） |

---

## ネクストアクション（次回セッションでやること）

### 即座にできること（Phase 0）

#### A. post_id マッピングテーブルの取得

```bash
PYTHON="C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\Scripts\python"
cd "C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit"

$PYTHON scripts/wp_reader.py --client naimono --action pages
$PYTHON scripts/wp_reader.py --client naimono --action posts
```

以下のURL群の post_id を特定する必要がある:
- `/faqs/faq1〜6`, `/gallerys/item_house`, `/item_ticket`, `/item_adviser`
- `/news`, `/news/20190925`, `/online`, `/business`, `/biz`
- `/campus_list`, `/es-info`, `/contact`, `/house`, `/ticket`, `/event`

#### B. 実行用 fix JSON の生成

post_id 取得後、`wp_meta_updater.py` が読み込める形式の JSON を生成する:

```json
{
  "fixes": [
    {
      "post_id": 123,
      "post_type": "pages",
      "updates": {
        "canonical": "https://jo-katsu.com/faqs/faq1/"
      }
    }
  ]
}
```

#### C. ドライラン実行

```bash
$PYTHON scripts/wp_meta_updater.py --client naimono --plan reports/naimono_fix_phase1.json
```

（`--execute` なしなので書き込みゼロ。安全にbefore/afterを確認できる）

### クライアント確認が必要なこと

ナイモノの清宮さんまたは担当者に Slack `pj_cw_na_media` で以下を確認:

> jo-katsu.com のテクニカルSEO監査で、以下5ページに noindex（検索結果に表示しない設定）が入っていることを検出しました。意図的な設定かどうか教えてください。
>
> 1. `/news` — ニュース一覧ページ
> 2. `/online` — オンラインページ
> 3. `/business` — ビジネスページ
> 4. `/biz` — ビズページ（/businessとの関係は？）
> 5. `/news/20190925` — 2019年9月のニュースページ

### 開発者向け指示書の作成（Phase 3）

監査レポートの内容を元に、以下のCRITICAL項目について開発者向けの指示書を別途まとめる:

1. **TTFB改善**: Redis Object Cache導入、PHP OPcache有効化、CDN検討
2. **リダイレクトチェーン排除**: campus系内部リンクの正規化
3. **CLS修正**: トップページの画像width/height、フォントpreload
4. **GSCサイトマップ再提出**: campus/sitemap.xml の再生成・再登録

---

## 実行スケジュール（目安）

```
Week 0（2/27 — 今ここ）
  ✅ 監査完了
  ✅ 修正プラン作成
  ✅ 実行プラン作成
  ⬜ post_id 取得
  ⬜ クライアントへnoindex確認連絡

Week 1
  ⬜ Phase 1-1: canonical修正 10件（自動・低リスク）
  ⬜ Phase 1-2: 重複タイトル修正 4件（自動・低リスク）
  ⬜ Phase 3-4: GSCサイトマップ再提出（即日対応可）
  ⬜ CRITICAL指示書をナイモノ開発者へ提出

Week 2
  ⬜ Phase 2-1: noindex解除（確認結果に応じて）
  ⬜ Phase 2-2: メタディスクリプション追加 優先10件
  ⬜ MEDIUM指示書をナイモノ開発者へ提出

Week 3-4
  ⬜ 効果測定（/wp-audit-lighthouse + /wp-audit-index で再監査）
```

---

## 参照パス早見表

| 用途 | パス |
|------|------|
| 監査パッケージ | `C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit\` |
| 監査レポート群 | 同上 `reports\` |
| 実行プラン | 同上 `reports\naimono_fix_execution_plan_20260227.md` |
| Python venv | `C:\Users\rikit\Projects\1_パーソナルデータ\seo-machine\.venv\` |
| クライアント設定 | 同上 `config\clients.json` |
| 修正スクリプト | 同上 `scripts\wp_meta_updater.py` |
| ナイモノ分析フォルダ | `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\` |
