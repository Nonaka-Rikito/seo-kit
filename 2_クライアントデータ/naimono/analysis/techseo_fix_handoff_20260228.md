# ナイモノ テクニカルSEO修正 — 引き継ぎ書

**作成日**: 2026-02-28
**対象サイト**: https://jo-katsu.com
**担当**: 野中力斗
**次のアクション**: WPアプリパスワード再生成 → ドライラン → 本番適用

---

## 1. プロジェクト概要

jo-katsu.com（ナイモノ / スタキャリ）のテクニカルSEO監査を2026-02-27に完了。
現在は修正実行フェーズ。修正は4フェーズに分かれている。

| フェーズ | 内容 | 件数 | 手法 | 状態 |
|---------|------|------|------|------|
| Phase 1 | canonical不整合の修正（faqs/gallerys） | 9件 | `wp_meta_updater.py` 自動 | 計画書生成済み・未適用 |
| Phase 2 | 重複タイトルの修正（gallerys/faqs） | 3件 | `wp_meta_updater.py` 自動 | 計画書生成済み・未適用 |
| Phase 3 | パフォーマンス修正（リンク・画像・プラグイン） | 複数 | 新スクリプト自動 + mu-plugin | 未実行 |
| Phase 4 | サーバー・テーマ修正（開発者対応） | 5件 | 手動（指示書あり） | 未実行 |

---

## 2. 完了済み作業

### 2-1. 監査レポート（2026-02-27完了）
- **総合監査レポート**: `1_パーソナルデータ/wp-techseo-audit/reports/naimono_full_audit_20260227.md`
- **修正実行計画**: `1_パーソナルデータ/wp-techseo-audit/reports/naimono_fix_execution_plan_20260227.md`
- **クロールデータ**: `1_パーソナルデータ/wp-techseo-audit/reports/jo-katsu_com_crawl_20260227_170416.json`

### 2-2. 修正計画JSON（2026-02-28生成済み）
| ファイル | 内容 |
|---------|------|
| `reports/naimono_fix_phase1_canonical.json` | canonical修正9件（faqs×6、gallerys×3） |
| `reports/naimono_fix_phase2_titles.json` | 重複タイトル修正3件（gallerys×2、faqs×1） |

### 2-3. noindex確認Slackドラフト（生成済み・未送信）
確認対象4ページ：
- `/news`（post_id=16）— ニュース一覧
- `/online`（post_id=2702）— オンライン就活
- `/biz`（post_id=4344）— 法人向けLP（WPスラッグは `biz` のみ確認済み。`/business` はリダイレクト等の可能性あり）
- `/news/20190925` — 旧ニュースアーカイブ

### 2-4. 新規作成スクリプト（2026-02-28）
| ファイル | 用途 |
|---------|------|
| `scripts/wp_content_fixer.py` | 内部リンクtrailing slash修正・画像dimensions追加 |
| `scripts/wp_plugin_manager.py` | キャッシュ等プラグイン確認・有効化 |
| `reports/jo_katsu_perf_fixes.php` | mu-plugin（font-display/preload/JS defer） |

---

## 3. ブロッカーと未完了タスク

### ⚠️ ブロッカー: WPアプリパスワードが無効

`seo-machine` ユーザーのアプリパスワードが無効になっており、WP REST API経由での書き込みが不可。
**Phase 1〜3の全スクリプトが、このパスワードが有効でないと実行できない。**

#### ユーザーが対応すること（タスクA）

1. WordPress管理画面にログイン → **ユーザー** → `seo-machine` → **アプリパスワード**
2. 既存パスワードを削除して**新規生成**
3. 生成されたパスワードを以下ファイルに更新:

```
ファイル: C:\Users\rikit\Projects\1_パーソナルデータ\wp-techseo-audit\config\.env
更新箇所: WP_NAIMONO_APP_PASSWORD=（新しいパスワードを貼り付け）
```

4. 接続確認（認証テスト）:
```bash
cd "/c/Users/rikit/Projects/1_パーソナルデータ/wp-techseo-audit"
PYTHON="/c/Users/rikit/Projects/1_パーソナルデータ/seo-machine/.venv/Scripts/python"
$PYTHON scripts/wp_meta_updater.py --client naimono --plan reports/naimono_fix_phase1_canonical.json
```
→ `Fix plan complete: N succeeded, 0 failed` の形式で、`failed=0` を確認できれば認証OK

---

## 4. 次のセッションでやること（順番通りに実行）

### ステップ1: ドライラン（タスクB）— 認証修正後すぐ実行

```bash
cd "/c/Users/rikit/Projects/1_パーソナルデータ/wp-techseo-audit"
PYTHON="/c/Users/rikit/Projects/1_パーソナルデータ/seo-machine/.venv/Scripts/python"

# Phase 1: canonical修正 9件
$PYTHON scripts/wp_meta_updater.py --client naimono --plan reports/naimono_fix_phase1_canonical.json

# Phase 2: 重複タイトル修正 3件
$PYTHON scripts/wp_meta_updater.py --client naimono --plan reports/naimono_fix_phase2_titles.json

# Phase 3a: プラグイン状態確認
$PYTHON scripts/wp_plugin_manager.py --client naimono --action check-perf

# Phase 3b: 内部リンクtrailing slash確認（campusページ）
PYTHONIOENCODING="utf-8" $PYTHON scripts/wp_content_fixer.py --client naimono --action fix-links --post-type campus

# Phase 3c: 画像dimensions確認（posts）
$PYTHON scripts/wp_content_fixer.py --client naimono --action fix-images --post-type posts
```

**確認ポイント**:
- `wp_meta_updater.py`: `Fix plan complete: N succeeded, 0 failed` になっているか
- `wp_content_fixer.py`: before/after が正しく表示されるか

### ステップ2: 本番適用（タスクC）— ドライラン結果確認・ユーザー承認後のみ

```bash
cd "/c/Users/rikit/Projects/1_パーソナルデータ/wp-techseo-audit"
PYTHON="/c/Users/rikit/Projects/1_パーソナルデータ/seo-machine/.venv/Scripts/python"

# Phase 1
$PYTHON scripts/wp_meta_updater.py --client naimono --plan reports/naimono_fix_phase1_canonical.json --execute

# Phase 2
$PYTHON scripts/wp_meta_updater.py --client naimono --plan reports/naimono_fix_phase2_titles.json --execute

# Phase 3b: 内部リンク修正
PYTHONIOENCODING="utf-8" $PYTHON scripts/wp_content_fixer.py --client naimono --action fix-links --post-type campus --execute

# Phase 3c: 画像dimensions修正
$PYTHON scripts/wp_content_fixer.py --client naimono --action fix-images --post-type posts --execute

# Phase 3d: キャッシュプラグイン導入（check-perfの結果を見てから判断）
# $PYTHON scripts/wp_plugin_manager.py --client naimono --action install --slug redis-cache --execute
```

⚠️ **`--execute` は必ずユーザーが「実行してください」と明示してから使うこと**

### ステップ3: mu-plugin アップロード（タスクD）— Phase 3の仕上げ

1. `reports/jo_katsu_perf_fixes.php` を開く
2. ファイル内の `$preload_resources` にLCP画像のURLを設定（DevToolsで確認）
3. テーマのH1セレクタを確認してCSS部分を調整
4. FTP/SFTP または WordPressファイルマネージャー で以下に配置:
   ```
   wp-content/mu-plugins/jo_katsu_perf_fixes.php
   ```
5. サイトにアクセスして表示崩れがないか確認

### ステップ4: noindex確認メッセージ送信

以下のSlackドラフトを送信する（送信先: 霜田さん or 清宮さん / チャンネル: `pj_cw_na_media`）:

```
お疲れ様です。野中です。

先日のテクニカルSEO監査の結果、いくつかのページにnoindex設定が入っていることを確認しました。
意図的な設定かどうか確認させてください。

【noindex確認が必要なページ（4件）】

① /news（ニュース一覧）
　└ インデックスされていません。ニュース一覧として検索流入を狙う場合はnoindex解除を推奨します。

② /online（オンライン就活ページ）
　└ インデックスされていません。集客対象ページであれば解除をご検討ください。

③ /business または /biz（法人向けページ）
　└ 法人向けLPとして意図的にnoindexにしている可能性がある旨を確認させてください。

④ /news/20190925（2019年9月の旧ニュース）
　└ 古い記事のためnoindex自体は問題ありません。意図的であれば現状維持でOKです。

各ページについて「意図的なnoindex」か「設定ミス」かを教えていただけますか？
確認後、必要なページのnoindex解除を対応します。

よろしくお願いいたします。
```

### ステップ5: 開発者向け指示書の送付（タスクE）

`techseo_dev_instructions_20260228.md`（同ディレクトリ）をナイモノ開発担当者に送付。
対応依頼項目: サーバーパフォーマンス / H1テーマ修正 / サイトマップ再提出

---

## 5. 修正内容の詳細

### Phase 1: canonical修正（9件）

faqs・gallerysカスタム投稿タイプのcanonical URLが旧パーマリンク構造（アクセス不能）を指している。

| post_id | post_type | slug | 現canonical | 修正後canonical |
|---------|-----------|------|-------------|----------------|
| 10 | faqs | faq1 | /faq/faqs/faq1/ | /faqs/faq1/ |
| 11 | faqs | faq2 | /faq/faqs/faq2/ | /faqs/faq2/ |
| 12 | faqs | faq3 | /faq/faqs/faq3/ | /faqs/faq3/ |
| 13 | faqs | faq4 | /faq/faqs/faq4/ | /faqs/faq4/ |
| 14 | faqs | faq5 | /faq/faqs/faq5/ | /faqs/faq5/ |
| 15 | faqs | faq6 | /faq/faqs/faq6/ | /faqs/faq6/ |
| 2 | gallerys | item_house | /gallery/gallerys/item_house/ | /gallerys/item_house/ |
| 3 | gallerys | item_ticket | /gallery/gallerys/item_ticket/ | /gallerys/item_ticket/ |
| 7 | gallerys | item_adviser | /gallery/gallerys/item_adviser/ | /gallerys/item_adviser/ |

### Phase 2: 重複タイトル修正（3件）

> ⚠️ **注意**: post_id 2, 3, 13 は Phase 1（canonical修正）と Phase 2（タイトル修正）の**両方の対象**。必ず Phase 1 を適用してから Phase 2 を実行すること。

| post_id | post_type | slug | 現タイトル | 修正後タイトル |
|---------|-----------|------|-----------|--------------|
| 2 | gallerys | item_house | ジョーカツハウス \| ジョーカツ | ジョーカツハウス フォトギャラリー \| ジョーカツ |
| 3 | gallerys | item_ticket | ジョーカツ切符 \| ジョーカツ | ジョーカツ切符 フォトギャラリー \| ジョーカツ |
| 13 | faqs | faq4 | ジョーカツイベント \| ジョーカツ | よくある質問（イベント）\| ジョーカツ |

**スキップ**: `/news/20190925` — WordPressアーカイブページのためpost_idなし、wp_meta_updater.py非対応

### Phase 3: パフォーマンス修正（スクリプト対応）

| 修正ID | 内容 | スクリプト | コマンド |
|-------|------|-----------|---------|
| FIX-002a | 内部リンクtrailing slash正規化 | `wp_content_fixer.py` | `--action fix-links --post-type campus` |
| FIX-003a | 画像のwidth/height属性追加 | `wp_content_fixer.py` | `--action fix-images --post-type posts` |
| FIX-003b | font-display:swap / preload | `jo_katsu_perf_fixes.php` | mu-plugin配置（手動1回） |
| FIX-001 | キャッシュプラグイン導入 | `wp_plugin_manager.py` | `--action install --slug redis-cache` |
| FIX-013 | 不要JS遅延読み込み | `jo_katsu_perf_fixes.php` | mu-plugin内で有効化フラグをtrueに |

### Phase 4: 開発者対応（指示書あり）

詳細は `techseo_dev_instructions_20260228.md` を参照。
※ `FIX-001` は同指示書で `FIX-001a` / `FIX-001b` に分割記載。

| 修正ID | 内容 | 深刻度 | SLA |
|-------|------|--------|-----|
| FIX-001 | PHP OPcache 有効化・Redis設定 | CRITICAL | 1週間 |
| FIX-002 | リダイレクトチェーン根本解消（campus DBクエリ調査） | CRITICAL | 1週間 |
| FIX-003 | トップページ CLS 修正（スライダー・画像サイズ） | CRITICAL | 1週間 |
| FIX-006 | GSCサイトマップ再提出 | HIGH | 即日 |
| FIX-008 | H1重複のテーマ修正（header.php） | MEDIUM | 1ヶ月 |

---

## 6. 関連ファイル一覧

```
wp-techseo-audit/
├── config/
│   └── .env                                  ← WP_NAIMONO_APP_PASSWORD を更新すること
├── reports/
│   ├── naimono_fix_phase1_canonical.json     ← Phase1実行計画（canonical修正9件）
│   ├── naimono_fix_phase2_titles.json        ← Phase2実行計画（タイトル修正3件）
│   ├── jo_katsu_perf_fixes.php               ← Phase3 mu-plugin（配置前にURL設定を要編集）
│   ├── naimono_full_audit_20260227.md        ← 総合監査レポート
│   └── jo-katsu_com_crawl_20260227_170416.json ← クロールデータ（詳細参照用）
└── scripts/
    ├── wp_meta_updater.py                    ← Phase1/2: メタ修正
    ├── wp_content_fixer.py                   ← Phase3: リンク・画像修正（新規）
    └── wp_plugin_manager.py                  ← Phase3: プラグイン管理（新規）

2_クライアントデータ/naimono/analysis/
├── techseo_fix_handoff_20260228.md           ← このファイル
└── techseo_dev_instructions_20260228.md      ← 開発者向け指示書
```

---

## 7. よくある質問

**Q: ドライランは安全？**
A: `--execute` なしのドライランは書き込みゼロ。WP側に一切変更を加えない。

**Q: Phase 1とPhase 2、どちらを先に適用すべき？**
A: Phase 1（canonical修正）を先に適用するのが推奨。canonicalが正しくなってからタイトルを修正する。ただし両方を同じセッションで続けて実行しても問題ない。

**Q: ロールバックは可能？**
A: `wp_meta_updater.py` は `--execute` 実行時に自動でロールバックJSONを生成する（同ディレクトリに `rollback_{timestamp}.json`）。ロールバックが必要な場合は、この自動生成ファイルを `--plan` に渡して `--execute` 付きで実行する。`--rollback` フラグは存在しない。

```bash
$PYTHON scripts/wp_meta_updater.py --client naimono --plan reports/rollback_YYYYMMDDTHHMMSSZ.json --execute
```

補足: Phase 1/2 は `faqs` / `gallerys` のカスタム投稿タイプを含むため、ロールバックJSON内の `post_type` が実データと一致していることを実行前に確認すること。不一致の場合はJSONを修正してから実行し、判断が難しい場合はWP管理画面で手動復旧する。

**Q: mu-pluginを配置して表示が崩れたら？**
A: `wp-content/mu-plugins/jo_katsu_perf_fixes.php` を削除すれば即時元に戻る。ファイルを削除するだけでOK。

**Q: wp_content_fixer.py のロールバックは？**
A: 現バージョンはロールバックJSONを生成しない。ドライランで変更内容を十分確認してから `--execute` すること。
