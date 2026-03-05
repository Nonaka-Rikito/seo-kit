# テクニカルSEO修正指示書 レビュー結果

**対象ファイル**: `techseo_dev_instructions_20260228.md`
**レビュー日**: 2026-02-28
**観点**: コマンド互換性 / WordPress推奨実装 / セキュリティ / 検証手順

---

## 重大度: CRITICAL（即修正必須）

### 1. FIX-008: `the_title` フィルターの誤用 — 実装が機能しない

**問題**: 子テーマでの対応として `add_filter('the_title', 'fix_site_title_heading', 10, 2);` を提案している。

**理由**: `the_title` フィルターは**投稿・固定ページのタイトル**にのみ適用される。ヘッダーのサイトタイトル（`bloginfo('name')` や `<h1 class="site-title">`）には一切影響しない。この実装では H1 重複は解消されず、代わりに全投稿のタイトル表示が意図せず変更されるリスクがある。

**修正案**:
```php
// 誤: the_title はサイトタイトルに無関係
// add_filter('the_title', 'fix_site_title_heading', 10, 2);

// 正: 子テーマに header.php をコピーし、<h1> を <p> に直接修正する。
// または、テーマが get_custom_logo() / custom_logo 等を使っている場合は
// 該当テーマのドキュメントを確認し、適切なフィルター（例: bloginfo 等）を利用する。
```
子テーマに `header.php` をコピーして `<h1>` を `<p>` に置換する方法を「唯一確実な方法」として明記し、`the_title` の記述は削除する。

---

### 2. FIX-001a: CONCATENATE_SCRIPTS と OPcache の誤った関連付け

**問題**: 「OPcache ヒット率向上」として `define('CONCATENATE_SCRIPTS', false);` を wp-config.php に追記するよう指示している。

**理由**: `CONCATENATE_SCRIPTS` は管理画面の JS/CSS 結合の有無を制御するもので、**OPcache とは無関係**。`false` にするとスクリプトが個別読み込みになり、リクエスト数が増え、パフォーマンスが悪化する場合がある。OPcache の効果を打ち消す可能性がある。

**修正案**: 該当ブロック（3. WordPress 側の最適化設定）を削除するか、次のように修正する。
```php
// OPcache は php.ini で有効化すること。以下は管理画面の JS エラー対策用（必要な場合のみ）
// define('CONCATENATE_SCRIPTS', false);  // プラグイン競合時のみ使用。通常は不要。
```

---

### 3. opcache-check.php: セキュリティリスクと削除忘れ

**問題**: `opcache_get_status()` をそのまま `var_dump` で出力する診断ファイルをルートに配置するよう指示している。

**理由**: サーバー内部のパス・メモリ使用量・設定値などが露出する。削除忘れや、第三者によるアクセスで情報漏洩のリスクがある。

**修正案**:
```php
<?php
// opcache-check.php — アクセス後は必ず削除すること
if (php_sapi_name() === 'cli' || (isset($_SERVER['REMOTE_ADDR']) && $_SERVER['REMOTE_ADDR'] === '127.0.0.1')) {
    if (function_exists('opcache_get_status')) {
        header('Content-Type: application/json');
        echo json_encode(opcache_get_status(), JSON_PRETTY_PRINT);
    } else {
        echo 'OPcache not available';
    }
} else {
    http_response_code(403);
    exit('Access denied');
}
```
または「SSH で `php -r "var_dump(opcache_get_status());"` を実行する」方法を推奨し、Web 公開を避ける。

---

## 重大度: HIGH（早めに修正推奨）

### 4. grep / cat コマンドの OS 依存（Windows 非対応）

**問題**: 以下のコマンドが Unix/Linux 専用で、Windows の cmd/PowerShell では動作しない。

- L156-161: `grep -r "\/campus\/[0-9]" wp-content/themes/ --include="*.php"`
- L269: `cat wp-content/themes/（テーマ名）/header.php | grep -A 5 "site-title\|site-branding"`

**理由**: 開発者が Windows 環境で作業する場合、そのまま実行できず手順が止まる。また `（テーマ名）` が日本語のままになっており、プレースホルダーとして分かりにくい。

**修正案**:
```bash
# Unix / Git Bash / WSL の場合
grep -r "\/campus\/[0-9]" wp-content/themes/ --include="*.php"
grep -r "\/campus\/[0-9]" wp-content/plugins/ --include="*.php"

# Windows PowerShell の場合
Get-ChildItem -Path wp-content/themes -Recurse -Include *.php | Select-String -Pattern "/campus/[0-9]"
Get-ChildItem -Path wp-content/themes\<テーマ名> -Filter header.php | Select-String -Pattern "site-title|site-branding" -Context 0,5
```
プレースホルダーは `（テーマ名）` → `<テーマ名>` または `{theme-name}` に統一し、「使用中のテーマ名は 外観 → テーマ で確認」と注記する。

---

### 5. TTFB 目標値の矛盾

**問題**: L42 で「目標は 200ms 以下」、L85 で「TTFB が 600ms 以下に改善されることを確認」と記載されており、数値が一致していない。

**理由**: 開発者がどちらを達成目標とするか判断できず、検証基準が曖昧になる。

**修正案**: 目標を一本化する。例: 「TTFB を 600ms 以下に改善（理想は 200ms 以下）」など、段階的な目標を明記する。

---

### 6. Lighthouse コマンドの前提不足

**問題**: `lighthouse https://jo-katsu.com --preset=perf --output=json` のみ記載され、実行環境の前提が書かれていない。

**理由**: `lighthouse` はグローバルインストールされていないことが多く、`npx lighthouse` が必要。`--preset=perf` は lighthouse-ci のオプションであり、標準 lighthouse CLI では `--only-categories=performance` を使う場合がある。そのまま実行するとエラーになる可能性がある。

**修正案**:
```bash
# Node.js がインストールされていること。初回は npx がパッケージを取得する
npx lighthouse https://jo-katsu.com --only-categories=performance --output=json --output-path=./report.json
```
実行前に `node -v` で Node.js の有無を確認する手順を追加する。

---

## 重大度: MEDIUM（運用時に注意）

### 7. FIX-003: preload の esc_url 未使用

**問題**: L234 の `echo '<link rel="preload" href="...">'` で、URL をそのまま出力している。

**理由**: 現状はハードコードなので即時リスクは低いが、将来変数化した際に XSS の余地が残る。WordPress の推奨は `esc_url()` の使用。

**修正案**:
```php
$font_url = 'https://fonts.gstatic.com/s/notosansjp/v52/xxx.woff2';
echo '<link rel="preload" href="' . esc_url($font_url) . '" as="font" type="font/woff2" crossorigin="anonymous">' . "\n";
```

---

### 8. FIX-002: リダイレクト解消の検証手順不足

**問題**: curl で確認するよう書いてあるが、「修正後どうあるべきか」の期待結果が明示されていない。

**理由**: 301 が 1 回だけなのか、200 で直接表示されるべきなのかが分からず、完了判定ができない。

**修正案**: 完了確認として以下を追加する。
- 修正前: `curl -I https://jo-katsu.com/campus/37260` → 301 が返る
- 修正後: 内部リンクがすべて `/campus/37260/`（trailing slash あり）になっているため、直接アクセスで 200 が返る、または 301 が 1 回のみになることを確認する

---

### 9. FIX-003: CLS の検証方法が未記載

**問題**: CLS 修正の「完了確認」に、CLS の計測方法が書かれていない。

**理由**: 修正後の効果を確認できず、目標 0.1 未満の達成状況が不明になる。

**修正案**: 完了確認として以下を追加する。
- PageSpeed Insights（モバイル）で CLS を確認
- Chrome DevTools → Performance タブで「Experience」の Cumulative Layout Shift を確認
- 目標: CLS 0.1 未満

---

### 10. Redis のホスト設定

**問題**: `define('WP_REDIS_HOST', '127.0.0.1');` を固定で記載している。

**理由**: マネージドホストや Redis の共有環境では、ホストが異なる場合がある。そのまま貼ると接続エラーになる可能性がある。

**修正案**: 「サーバー提供元のマニュアルで Redis の接続先を確認する」旨を追記し、`127.0.0.1` は例として記載する。

---

## 重大度: LOW（改善推奨）

### 11. FIX-008: トップページの H1 扱い

**問題**: サイトタイトルを全ページで `<p>` に変更するよう指示しているが、トップページではサイトタイトルがメインの見出しとして `<h1>` であることが妥当な場合がある。

**理由**: トップページのみ `<h1>` を残し、その他を `<p>` にする方が SEO の観点で適切な場合がある。テーマの構造によって判断が分かれる。

**修正案**: 「トップページのみ `<h1>` を残し、それ以外は `<p>` にする」という選択肢を注記として追加する。

---

### 12. 子テーマの functions.php の関数名

**問題**: 299 行目で `fix_site_title_heading` が参照されているが、実際の関数定義はない（かつ、the_title フィルターは誤りなので削除推奨）。

**理由**: 実装が不完全なまま残っていると、誤った実装に繋がる。

**修正案**: 該当ブロック（3. 子テーマでの対応）を削除するか、正しい方法（header.php のコピー）に置き換える。

---

## 修正優先度サマリー

| 優先度 | 項目 | 対応 |
|--------|------|------|
| 1 | the_title フィルター誤用 | 削除し、子テーマでの header.php 修正を明記 |
| 2 | CONCATENATE_SCRIPTS | 削除または注記で「OPcache と無関係」と明記 |
| 3 | opcache-check.php セキュリティ | IP 制限または CLI 実行を推奨 |
| 4 | grep/cat の OS 依存 | PowerShell 代替コマンドを追加 |
| 5 | TTFB 目標値 | 600ms / 200ms を整理して統一 |
| 6 | Lighthouse コマンド | npx と --only-categories を明記 |
| 7〜10 | その他 | 上記修正案に従って追記・修正 |

---

*本レビューは開発者実装目線での指摘です。文言の最終調整は malna 側で行ってください。*
