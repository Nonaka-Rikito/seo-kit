# ナイモノ（jo-katsu.com）テクニカルSEO修正 — 開発者向け指示書

**作成日**: 2026-02-28
**作成者**: 野中力斗（malna株式会社）
**対象サイト**: https://jo-katsu.com
**依頼先**: ナイモノ 開発担当者

---

## 概要

2026-02-27に実施したテクニカルSEO監査の結果、**サーバー設定・テーマファイルの修正が必要な項目**が検出されました。
これらはWordPress管理画面やAPIからは対応できないため、開発担当者の方にご対応をお願いします。

対応項目は優先度順に記載しています。**CRITICAL（即対応）の4件**を優先してください。

---

## 対応項目一覧

| # | 修正ID | 内容 | 深刻度 | 期限 |
|---|-------|------|--------|------|
| 1 | FIX-001a | PHP OPcache の有効化確認 | CRITICAL | 1週間 |
| 2 | FIX-001b | サーバーキャッシュの設定（Redis または ページキャッシュ） | CRITICAL | 1週間 |
| 3 | FIX-002 | campusページのリダイレクトチェーン解消 | CRITICAL | 1週間 |
| 4 | FIX-003 | トップページ CLS 修正（スライダー・ヒーロー画像） | CRITICAL | 1週間 |
| 5 | FIX-006 | GSC サイトマップ再提出 | HIGH | 即日 |
| 6 | FIX-014 | テキスト圧縮の有効化（gzip / brotli） | HIGH | 即日 |
| 7 | FIX-008 | H1 タグ重複修正（header.php） | MEDIUM | 1ヶ月 |

---

## 詳細

---

### FIX-001a: PHP OPcache の有効化確認

**深刻度**: CRITICAL
**期限**: 1週間
**影響**: TTFB（Time to First Byte）の改善。全ページの応答速度に直結。

#### 現状の問題
監査で TTFB 平均 **1,271ms** を確認。まずは 600ms 以下まで改善し、理想値として 200ms 以下を目指す。
PHP OPcache が無効の場合、毎リクエストで PHP ファイルがコンパイルされ遅延が発生する。

#### 対応手順

**1. OPcache の有効化確認**

サーバーの `php.ini`（または `conf.d/` 配下の設定ファイル）を確認:

```ini
[opcache]
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=8
opcache.max_accelerated_files=10000
opcache.revalidate_freq=2
opcache.save_comments=1
```

**2. 現在の状態確認（推奨: CLI）**

SSH で以下を実行:

```bash
php -r "var_dump(function_exists('opcache_get_status') ? opcache_get_status(false) : 'OPcache not available');"
```

Web経由での確認が必要な場合のみ、一時ファイルを使う:

```php
<?php
// ファイル名: opcache-check.php
// WordPress ルートに一時配置。アクセス後は必ず削除すること。
// 127.0.0.1 / ::1 以外はアクセス拒否。
$remote_addr = $_SERVER['REMOTE_ADDR'] ?? '';
if ($remote_addr !== '127.0.0.1' && $remote_addr !== '::1') {
    http_response_code(403);
    exit('Access denied');
}

if (function_exists('opcache_get_status')) {
    header('Content-Type: application/json; charset=utf-8');
    echo wp_json_encode(opcache_get_status(false), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
} else {
    echo 'OPcache not available';
}
```

確認後、ファイルは必ず削除してください。

#### 完了確認
- TTFB が 600ms 以下に改善されることを確認（理想値: 200ms 以下）
- PageSpeed Insights（モバイル）でスコアが改善されることを確認

---

### FIX-001b: サーバーキャッシュの設定

**深刻度**: CRITICAL
**期限**: 1週間
**影響**: ページキャッシュにより TTFB を大幅削減（動的生成 → 静的配信）。

#### 選択肢

**案A: Redis Object Cache（推奨 — サーバーに Redis がある場合）**

1. サーバー側で Redis が起動しているか確認:
   ```bash
   redis-cli ping
   # → PONG が返れば OK
   ```

2. WordPress プラグイン `Redis Object Cache` をインストール・有効化
   （malna側でAPI経由での有効化を試みる。サーバー側でRedisが起動していれば自動接続される）

3. `wp-config.php` に以下を追記:
   ```php
   // 値はサーバー環境に合わせる（127.0.0.1 は例）
   define('WP_REDIS_HOST', '127.0.0.1');
   define('WP_REDIS_PORT', 6379);
   define('WP_CACHE', true);
   ```

**案B: W3 Total Cache または WP Super Cache（Redis がない場合）**

1. サーバーのディレクトリ書き込み権限を確認:
   - `wp-content/cache/` に書き込み可能か
2. プラグイン設定で「ページキャッシュ」を有効化
3. `.htaccess` ベースのキャッシュが使用できるか確認（Apache の場合）

#### 注意事項
- キャッシュ導入後、ログイン中ユーザーには動的ページを表示するよう設定すること
- WooCommerce 等のカート・決済ページはキャッシュ除外設定が必要

---

### FIX-002: campusページのリダイレクトチェーン解消

**深刻度**: CRITICAL
**期限**: 1週間
**影響**: モバイルLCPが **30秒超**。リダイレクトチェーンが主要因のひとつ。

#### 現状の問題
`/campus/` 配下のページへのアクセスに trailing slash なしのURL（例: `/campus/37260`）が内部リンクで使われており、`/campus/37260/` へ 301 リダイレクトが発生している。
これが連鎖して LCP の計測時間に大きく影響している。

#### 対応手順

**1. 現在のリダイレクト状況確認**

ブラウザの DevTools（Network タブ）または curl で確認:
```bash
curl -I https://jo-katsu.com/campus/37260
# → 301 の Location ヘッダーが返るか確認
```

**2. WordPress の Permalink 設定確認**

管理画面 → 設定 → パーマリンク → 「投稿名」が選択されているか確認。
変更後は「変更を保存」ボタンを一度押すだけで `.htaccess` が更新される。

**3. テーマ・プラグイン内の内部リンク修正**

`/campus/` への内部リンクで trailing slash なしのURLを使っている箇所を検索:

```bash
# Unix / Git Bash / WSL
# テーマディレクトリ内を検索
grep -r "\/campus\/[0-9]" wp-content/themes/ --include="*.php"

# プラグインディレクトリ内を検索
grep -r "\/campus\/[0-9]" wp-content/plugins/ --include="*.php"
```

```powershell
# Windows PowerShell
Get-ChildItem -Path wp-content/themes -Recurse -Include *.php | Select-String -Pattern "/campus/[0-9]"
Get-ChildItem -Path wp-content/plugins -Recurse -Include *.php | Select-String -Pattern "/campus/[0-9]"
```

見つかった箇所は trailing slash ありの URL（`/campus/37260/`）に修正する。
修正後は `curl -I https://jo-katsu.com/campus/37260/` で 200 応答になること（または不要な多段リダイレクトが解消されていること）を確認する。

**4. DBクエリのプロファイリング（TTFB 根本原因調査）**

`Query Monitor` プラグインを一時的に有効化し、campusページのDBクエリ数・時間を確認。
以下に該当する場合は最適化が必要:
- 単ページで 50クエリ以上
- 1クエリで 100ms 以上かかっているものがある

確認後、プラグインは無効化してください。

---

### FIX-003: トップページ CLS 修正

**深刻度**: CRITICAL
**期限**: 1週間
**影響**: トップページ CLS **0.282**（目標: 0.1 未満）。ページ読み込み時にコンテンツがずれる。

#### 現状の問題
ヒーロー画像・スライダー・Webフォントの読み込み遅延により、レイアウトシフトが発生している。

#### 対応手順

**1. ヒーロー画像・バナーに width / height 属性を追加**

テーマの `header.php`、`index.php`、`front-page.php` 内の `<img>` タグを確認:

```html
<!-- 修正前 -->
<img src="/wp-content/themes/xxx/images/hero.jpg" alt="ヒーロー画像">

<!-- 修正後 -->
<img src="/wp-content/themes/xxx/images/hero.jpg" alt="ヒーロー画像" width="1920" height="800">
```

`width` / `height` は実際の画像サイズに合わせること。

**2. スライダー・カルーセルのプレースホルダー確保**

スライダーが読み込まれる前のスペースを CSS で確保する:

```css
/* スライダーコンテナに固定アスペクト比を設定 */
.hero-slider,
.top-slider {
    aspect-ratio: 16 / 9;  /* または width/height で明示 */
    min-height: 400px;     /* フォールバック */
}

/* または padding-top ハック（古いブラウザ対応） */
.slider-wrapper {
    position: relative;
    padding-top: 56.25%; /* 16:9 = 9/16 × 100 */
}
.slider-wrapper .slide {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
}
```

**3. Webフォントに font-display: swap を設定**

`functions.php` 内の Google Fonts 読み込み箇所を確認:

```php
// 修正前
wp_enqueue_style('google-fonts', 'https://fonts.googleapis.com/css2?family=Noto+Sans+JP');

// 修正後
wp_enqueue_style('google-fonts', 'https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap');
```

> 注: malna側が mu-plugin で自動付与する設定を入れているため、
> functions.php から読み込んでいる場合は二重適用にならないか確認すること。

**4. フォントの preload 設定**

テーマの `functions.php` または `wp_head` フックで追加:

```php
add_action('wp_head', function() {
    // 使用しているフォントファイルのURLを実際のものに変更すること
    $font_url = 'https://fonts.gstatic.com/s/notosansjp/v52/xxx.woff2';
    echo '<link rel="preload" href="' . esc_url($font_url) . '" as="font" type="font/woff2" crossorigin="anonymous">' . "\n";
}, 1);
```

フォントファイルのURLは DevTools の Network タブ → Font フィルターで確認できる。

---

### FIX-006: GSC サイトマップ再提出

**深刻度**: HIGH
**期限**: 即日対応
**影響**: `campus/sitemap.xml` が1年7ヶ月間 Google にダウンロードされていない。campusページのインデックス漏れに直結。

#### 対応手順

**1. サイトマップの存在確認**

ブラウザで以下にアクセスしてサイトマップが表示されるか確認:
```
https://jo-katsu.com/campus/sitemap.xml
https://jo-katsu.com/sitemap.xml
https://jo-katsu.com/sitemap_index.xml
```

**2. Yoast SEO でサイトマップを再生成**

管理画面 → Yoast SEO → 一般 → 機能 → XML サイトマップ → 「?」をクリック → 「XML サイトマップを見る」でアクセスできるか確認。

表示されない場合: Yoast SEO を一度無効化 → 再有効化でサイトマップが再生成される。

**3. Google Search Console で再提出**

1. GSC にログイン（malna または ナイモノ担当者）
2. サイトマップ → 既存のサイトマップを削除
3. 新しいサイトマップURLを入力して送信
4. ステータスが「成功」になることを確認

---

### FIX-014: テキスト圧縮の有効化（gzip / brotli）

**深刻度**: HIGH
**期限**: 即日
**影響**: HTML/CSS/JS のレスポンスサイズを 60〜80% 削減。TTFB・転送量・FCP すべてに即効性あり。

#### 現状の問題

PSI の診断に「テキスト圧縮を有効にする」が出ており、現在サーバーからのレスポンスが非圧縮で配信されている。

#### 対応手順

**Apache の場合（.htaccess）**

WordPress ルートの `.htaccess` に以下を追記（`# BEGIN WordPress` の前に追記すること）:

```apache
# テキスト圧縮（gzip）
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css
    AddOutputFilterByType DEFLATE text/javascript application/javascript application/x-javascript
    AddOutputFilterByType DEFLATE application/json application/xml application/xhtml+xml
    AddOutputFilterByType DEFLATE image/svg+xml font/ttf font/otf application/font-woff application/font-woff2
</IfModule>

# ブラウザキャッシュ（静的ファイル）
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/png  "access plus 1 year"
    ExpiresByType image/webp "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
    ExpiresByType text/css   "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
    ExpiresByType application/font-woff2 "access plus 1 year"
</IfModule>
```

**Nginx の場合（nginx.conf または サイト設定ファイル）**

```nginx
# gzip 圧縮
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied any;
gzip_comp_level 6;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/javascript
    application/json
    application/xml
    application/xhtml+xml
    image/svg+xml
    font/ttf
    font/otf
    application/font-woff
    application/font-woff2;

# brotli 圧縮（nginx-module-brotli が必要）
# brotli on;
# brotli_comp_level 6;
# brotli_types text/plain text/css application/javascript application/json;

# ブラウザキャッシュ
location ~* \.(jpg|jpeg|png|gif|webp|svg|woff2|woff|ttf)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
location ~* \.(css|js)$ {
    expires 1M;
    add_header Cache-Control "public";
}
```

#### 完了確認

```bash
# gzip が有効になっているか確認
curl -I -H "Accept-Encoding: gzip" https://jo-katsu.com/ | grep -i "content-encoding"
# → content-encoding: gzip が返れば OK

# または brotli の確認
curl -I -H "Accept-Encoding: br" https://jo-katsu.com/ | grep -i "content-encoding"
# → content-encoding: br が返れば OK
```

PageSpeed Insights で「テキスト圧縮を有効にする」の警告が消えることを確認。

---

### FIX-008: H1 タグ重複修正

**深刻度**: MEDIUM
**期限**: 1ヶ月
**影響**: 全92ページでH1が2個存在。Googleが主要見出しを正しく認識できない可能性。

#### 現状の問題
テーマの `header.php` でサイトタイトルが `<h1>` タグで出力されており、各ページのコンテンツH1と重複している。

#### 対応手順

**1. テーマの header.php を確認**

```bash
# 使用テーマのヘッダーファイルを確認
grep -nE "site-title|site-branding" wp-content/themes/<テーマ名>/header.php
```

```powershell
# Windows PowerShell
Get-Content "wp-content/themes/<テーマ名>/header.php" | Select-String -Pattern "site-title|site-branding" -Context 0,5
```

以下のようなパターンを探す:
```html
<h1 class="site-title">
    <a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>
</h1>
```

**2. h1 を span または p タグに変更**

```html
<!-- 修正後 -->
<p class="site-title">
    <a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>
</p>
```

> ⚠️ 子テーマを使用していない場合は、テーマ更新で変更が上書きされる。
> **子テーマを作成してから変更することを強く推奨する。**

**3. 子テーマでの対応（推奨）**

`the_title` フィルターはサイトタイトルの `<h1>` 変更には不向きのため使用しない。  
子テーマに `header.php` をコピーして `<h1 class="site-title">` を `<p class="site-title">` に変更する方法を採用する。

**4. H1 のない8ページに H1 を追加**

以下のページには H1 がない。テンプレートを確認して追加すること:
- `/`（トップページ）
- `/campus/`（campusアーカイブ）
- `/campus_list`（就活ハンドブック一覧）

---

## 修正完了後の確認依頼

各修正が完了したタイミングで野中（rikito.nonaka@malna.co.jp）までご連絡ください。
malna側でPageSpeed Insights・GSCの再確認を行います。

### 確認コマンド（malna側で実施）
```bash
# Lighthouse 再監査（修正後のスコア確認）
npx lighthouse https://jo-katsu.com --only-categories=performance --output=json --output-path=./lighthouse-performance.json

# GSC インデックス再確認（修正から数日後）
```

---

## 参考: 修正の優先順位と期待効果

| 優先 | 修正 | 期待効果 |
|-----|------|---------|
| 1位 | テキスト圧縮（gzip/brotli）有効化 | 転送量 60〜80% 削減・即日効果・PSI +5〜10pt |
| 2位 | OPcache 有効化 | TTFB 1,271ms → 600ms 以下（理想 200ms 以下、推定） |
| 3位 | ページキャッシュ導入（Redis / W3 Total Cache） | 実LCP 2.8s → 1.5s 以下（推定） |
| 4位 | リダイレクトチェーン解消 | ラボLCP 30s → 5s 以下（推定） |
| 5位 | CLS 修正 | トップページ CLS 0.282 → 0.1 以下 |
| 6位 | サイトマップ再提出 | campus記事のインデックス率改善 |
| 7位 | H1 修正 | 検索結果での見出し認識精度向上 |

---

*本指示書に不明点がある場合は野中（Slack: @野中力斗）までご連絡ください。*
