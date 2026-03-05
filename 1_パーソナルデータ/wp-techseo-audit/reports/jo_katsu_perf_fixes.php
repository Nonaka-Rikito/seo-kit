<?php
/**
 * Plugin Name: Jo-katsu.com パフォーマンス修正
 * Description: テクニカルSEO修正 — font-display:swap / LCP preload / H1重複CSS対処 / リダイレクトチェーン修正補助
 * Version: 1.0.0
 * Author: malna (wp-techseo-audit)
 *
 * ============================================================
 * 配置場所: wp-content/mu-plugins/jo_katsu_perf_fixes.php
 * ============================================================
 * mu-plugins に置くと WordPress が自動的に読み込む。
 * プラグインの有効化操作は不要。
 *
 * 対応修正:
 *   FIX-003: font-display: swap (Google Fonts CLS/レンダリング改善)
 *   FIX-003: LCP リソース preload (ヒーロー画像の優先読み込み)
 *   FIX-008: H1 重複 CSS 対処 (テーマのサイトタイトルH1を視覚的に無効化)
 *   FIX-013: JS defer/async 強制付与 (レンダーブロッキング削減)
 *
 * 注意:
 *   - このファイルは PHP テーマファイルを変更しない（安全）
 *   - H1 重複の根本修正はテーマの header.php 変更が必要（別途対応）
 *   - このファイルは CSS 注入と preload タグ追加のみ行う
 * ============================================================
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit; // 直接アクセス禁止
}

// ============================================================
// FIX-003: Google Fonts に font-display: swap を適用
// ============================================================
// Yoast や テーマが出力する Google Fonts URL に &display=swap を追記する

add_filter( 'style_loader_src', 'jokatsu_add_font_display_swap', 10, 2 );

function jokatsu_add_font_display_swap( $src, $handle ) {
    // Google Fonts URL にのみ適用
    if ( strpos( $src, 'fonts.googleapis.com' ) === false ) {
        return $src;
    }
    // すでに display= パラメータがある場合はスキップ
    if ( strpos( $src, 'display=' ) !== false ) {
        return $src;
    }
    $src = add_query_arg( 'display', 'swap', $src );
    return $src;
}


// ============================================================
// FIX-003: LCP リソース preload ヒント
// ============================================================
// ヒーロー画像・ロゴ等の LCP 候補リソースを <link rel="preload"> で優先読み込みする
//
// ★ カスタマイズ箇所:
//   下記 $preload_resources の src を実際のリソースに合わせて変更すること

add_action( 'wp_head', 'jokatsu_add_preload_hints', 1 );

function jokatsu_add_preload_hints() {
    // ★ 実際のLCP画像URLに変更すること（ブラウザのDevToolsで確認）
    $preload_resources = array(
        // ヒーロー画像（トップページのファーストビュー画像）
        // array(
        //     'href' => 'https://jo-katsu.com/wp-content/themes/your-theme/images/hero.jpg',
        //     'as'   => 'image',
        //     'type' => 'image/jpeg',
        // ),
        //
        // メインフォント（Webフォント使用の場合）
        // array(
        //     'href'        => 'https://fonts.gstatic.com/s/noto-sans-jp/v...',
        //     'as'          => 'font',
        //     'type'        => 'font/woff2',
        //     'crossorigin' => 'anonymous',
        // ),
    );

    foreach ( $preload_resources as $resource ) {
        $attrs = '';
        foreach ( $resource as $key => $value ) {
            $attrs .= ' ' . esc_attr( $key ) . '="' . esc_attr( $value ) . '"';
        }
        echo '<link rel="preload"' . $attrs . ' />' . "\n";
    }
}


// ============================================================
// FIX-008: H1 重複 CSS 対処
// ============================================================
// テーマのサイトタイトル H1 を CSS で視覚的に通常テキスト扱いにする。
// SEO 的にはH1タグが複数存在することへの根本修正ではないが、
// クローラーへの混乱を軽減する暫定対処。
//
// ★ 根本修正: テーマの header.php で <h1 class="site-title"> を
//   <div class="site-title"> または <p class="site-title"> に変更すること。

add_action( 'wp_head', 'jokatsu_fix_h1_duplicate_css', 5 );

function jokatsu_fix_h1_duplicate_css() {
    // サイトタイトルを格納している要素のセレクタを確認してから適用すること
    // 下記は一般的な WordPress テーマのパターン
    ?>
    <style id="jokatsu-h1-fix">
    /*
     * H1 重複対処: サイトロゴ/ヘッダーの H1 を視覚的に通常テキストとして扱う
     * テーマによってセレクタが異なる — DevTools で確認して調整すること
     *
     * よくあるセレクタ例:
     *   .site-title (Twenty Twenty-One 等)
     *   .header-title (カスタムテーマ)
     *   #site-title
     */

    /* ★ テーマのセレクタを確認して下記を適切に変更すること */
    /* .site-title h1,
    .site-branding h1 {
        font-size: inherit;
        font-weight: inherit;
        line-height: inherit;
        margin: 0;
    } */
    </style>
    <?php
}


// ============================================================
// FIX-013: JS に defer/async を付与（レンダーブロッキング削減）
// ============================================================
// wp_enqueue_script で登録されたスクリプトのうち、
// インラインスクリプト依存関係がなく body 出力のものに defer を付与する。
//
// 注意: jQuery やインタラクション系スクリプトに defer を付けると
//       動作が壊れる場合があるため、除外リストを確認してから有効化すること。
//
// ★ デフォルトは無効 (false)。確認後に true に変更して有効化すること。

define( 'JOKATSU_ENABLE_SCRIPT_DEFER', false );

if ( JOKATSU_ENABLE_SCRIPT_DEFER ) {
    add_filter( 'script_loader_tag', 'jokatsu_add_defer_to_scripts', 10, 3 );

    function jokatsu_add_defer_to_scripts( $tag, $handle, $src ) {
        // defer を付与しないスクリプト（除外リスト）
        $exclude_handles = array(
            'jquery',
            'jquery-core',
            'jquery-migrate',
            'wp-embed',
            // 追加する場合はここに handle 名を記載
        );

        if ( in_array( $handle, $exclude_handles, true ) ) {
            return $tag;
        }

        // すでに defer または async がある場合はスキップ
        if ( strpos( $tag, ' defer' ) !== false || strpos( $tag, ' async' ) !== false ) {
            return $tag;
        }

        // <script src=... を <script defer src=... に変更
        return str_replace( ' src=', ' defer src=', $tag );
    }
}


// ============================================================
// FIX-002 補助: trailing slash リダイレクトのログ
// ============================================================
// 内部リンクの trailing slash 不一致を検出してエラーログに記録する。
// wp_content_fixer.py のドライラン結果と合わせて確認用。
// ★ デフォルトは無効。診断時のみ有効化すること。

define( 'JOKATSU_LOG_REDIRECT_CHAINS', false );

if ( JOKATSU_LOG_REDIRECT_CHAINS && defined( 'WP_DEBUG_LOG' ) && WP_DEBUG_LOG ) {
    add_action( 'template_redirect', 'jokatsu_log_redirect_chain' );

    function jokatsu_log_redirect_chain() {
        $request_uri = $_SERVER['REQUEST_URI'] ?? '';
        // trailing slash なしのURLにアクセスがあった場合を記録
        if ( ! empty( $request_uri ) && substr( $request_uri, -1 ) !== '/' && strpos( $request_uri, '.' ) === false ) {
            error_log( '[jo-katsu perf] trailing slash missing: ' . esc_url( $request_uri ) );
        }
    }
}
