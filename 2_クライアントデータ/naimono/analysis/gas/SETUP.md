# バナー差替え検証システム — セットアップガイド

このドキュメントは Google Apps Script (GAS) を使ったバナー差替え効果測定システムの初期設定手順です。

---

## 前提条件

- Google アカウント
- GA4 プロパティへのアクセス権限
- Google Search Console へのアクセス権限
- Slack Workspace（通知用）

---

## セットアップ手順

### 1. Google フォームの作成

1. [Google Forms](https://forms.google.com/) を開く
2. 「空白のフォーム」を作成
3. フォームタイトル: 「バナー差替え記録」
4. 質問を追加:
   - 質問文: 「ページURL」
   - 回答形式: 「記述式」（短答）
   - 必須: ON
5. 右上の「送信」→「リンクをコピー」（後で使う）

### 2. フォーム回答をスプレッドシートに連携

1. フォーム編集画面で「回答」タブをクリック
2. 右上の「スプレッドシートにリンク」（緑のアイコン）をクリック
3. 「新しいスプレッドシートを作成」を選択 → 作成
4. 自動的に回答用スプレッドシートが開く

### 3. Apps Script プロジェクトの作成

1. 回答スプレッドシートを開いた状態で「拡張機能」→「Apps Script」をクリック
2. GAS エディタが開く
3. 左側のファイル一覧で以下を作成:
   - `Config.gs`
   - `Main.gs`
   - `GA4.gs`
   - `GSC.gs`
   - `Sheet.gs`
   - `Slack.gs`
   - `Utils.gs`
4. 各ファイルに対応するコードをコピー&ペースト
5. 左側メニューの「プロジェクトの設定」（歯車アイコン）→「appsscript.json をマニフェスト エディタで表示する」にチェック
6. 左のファイル一覧に表示される `appsscript.json` を開いて、該当コードで上書き

### 4. Advanced Services の有効化

1. GAS エディタ左側の「サービス」（+アイコン）をクリック
2. 以下の2つを追加:
   - **Google Analytics Data API** → バージョン: v1beta → 追加
   - **Google Search Console API** → バージョン: v3 → 追加

### 5. Config.gs の設定

`Config.gs` を開いて、以下の値を実際の値に置き換える:

```javascript
const CONFIG = {
  // GA4 プロパティ ID（数字のみ）
  // GA4 管理画面「管理」→「プロパティの設定」→「プロパティID」
  GA4_PROPERTY_ID: 'XXXXXXXXX',

  // GSC に登録しているサイトURL
  // Search Console で「プロパティを選択」の URL（末尾スラッシュに注意）
  GSC_SITE_URL: 'https://example.com/',

  // 回答スプレッドシートの ID
  // スプレッドシートのURL: https://docs.google.com/spreadsheets/d/{ここがID}/edit
  SPREADSHEET_ID: 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',

  // Slack Incoming Webhook URL
  // Slack の「管理」→「アプリを管理」→「Incoming Webhook」で作成
  SLACK_WEBHOOK_URL: 'https://hooks.slack.com/services/XXXXX/XXXXX/XXXXX',

  // ... 以下はデフォルトのままでOK
};
```

### 6. スプレッドシートの権限設定

1. GAS エディタで `testFormSubmit` 関数を実行してテスト:
   - `Main.gs` を開く
   - 上部の関数ドロップダウンから `testFormSubmit` を選択
   - 「実行」ボタンをクリック
2. 初回は「承認が必要です」ダイアログが表示される:
   - 「権限を確認」をクリック
   - Google アカウントを選択
   - 「詳細」→「〜〜に移動（安全ではないページ）」をクリック
   - 「許可」をクリック

### 7. トリガーの設定

1. GAS エディタ左側の「トリガー」（時計アイコン）をクリック
2. 右下の「トリガーを追加」をクリック
3. 以下のように設定:
   - **実行する関数**: `onFormSubmit`
   - **実行するデプロイ**: Head
   - **イベントのソース**: フォームから
   - **イベントの種類**: フォーム送信時
4. 「保存」

### 8. Slack Incoming Webhook の作成

1. Slack を開く
2. 左上のワークスペース名 → 「設定と管理」→「アプリを管理」
3. 検索で「Incoming Webhooks」を検索 → 追加
4. 通知を送信するチャンネルを選択（例: `#banner-verification`）
5. 表示された Webhook URL をコピーして `Config.gs` の `SLACK_WEBHOOK_URL` に設定

---

## 動作確認

### テスト 1: 手動実行でシステム全体をテスト

1. GAS エディタで `testFormSubmit` 関数を実行
2. 以下を確認:
   - スプレッドシートに「変更ログ」「データ」シートが自動作成される
   - 「変更ログ」シートに記録が追加される
   - 「データ」シートに Before データが記録される
   - Slack に通知が届く
   - GAS の「実行数」に時限トリガーが追加される

### テスト 2: Google フォームから送信

1. 最初に作成した Google フォームを開く
2. テスト用の記事URLを入力（例: `https://example.com/test-page`）
3. 送信
4. テスト1と同様の動作を確認

### テスト 3: レポート生成（14日後）

- 実際には14日後に自動実行されるが、テストする場合:
  1. `Utils.gs` の `listAllTriggers()` を実行してトリガーIDを確認
  2. `testGenerateReport()` 内のトリガーIDを実際のIDに書き換え
  3. 実行（※ 実際には After データが存在しないとエラーになる）

---

## トラブルシューティング

### GA4 Data API でエラーが出る

**エラー例**: `AnalyticsData is not defined`

**原因**: Advanced Service が有効化されていない

**解決策**:
1. GAS エディタ左側「サービス」→「Google Analytics Data API」を追加
2. `appsscript.json` に以下が含まれているか確認:
   ```json
   {
     "userSymbol": "AnalyticsData",
     "serviceId": "analyticsdata",
     "version": "v1beta"
   }
   ```

### GSC API でエラーが出る

**エラー例**: `Request had insufficient authentication scopes`

**原因**: OAuth スコープが不足している

**解決策**:
1. `appsscript.json` に以下が含まれているか確認:
   ```json
   "https://www.googleapis.com/auth/webmasters.readonly"
   ```
2. 一度トリガーを削除して再作成し、再度権限を付与

### データが取得できない（noData: true）

**原因**: ページURL や期間が間違っている、またはデータが存在しない

**確認事項**:
- GA4 で該当ページのデータが存在するか確認
- GSC で該当ページのデータが存在するか確認
- `pagePath` と `pageUrl` の違いに注意:
  - GA4: `/campus/26469` （パスのみ）
  - GSC: `https://example.com/campus/26469` （完全URL）

### トリガーが実行されない

**原因**: トリガーの設定ミス、または GAS の実行時間制限

**確認事項**:
- GAS エディタ「トリガー」でトリガーが正しく設定されているか確認
- GAS エディタ「実行数」でエラーログを確認
- 実行時間が6分を超える場合はタイムアウト（その場合は処理を分割）

---

## 運用

### 通常の使い方

1. バナーを差し替える（通常業務）
2. Google フォームに記事URLを入力して送信（**これだけ**）
3. 14日後に Slack でレポートが届く（自動）

### データの確認

- スプレッドシートの「ダッシュボード」シートで全履歴を確認（別途作成推奨）
- 「変更ログ」シートで差替え履歴を確認
- 「データ」シートで Before/After の生データを確認

### トリガーの管理

- GAS エディタ「トリガー」で予定されているレポート生成を確認
- 必要に応じて手動でトリガーを削除
- `listAllTriggers()` 関数でトリガー一覧を確認
- `deleteAllTriggers()` で全トリガーを削除（初期化時のみ）

---

## 次のステップ: Phase 2 への拡張

Phase 1 が安定稼働したら、以下の機能を追加できます:

1. **定期スクレイピングによる自動検知**
   - バナー画像の変更を自動で検知
   - フォーム入力すら不要になる

2. **中間レポート機能**
   - 7日後に速報値を通知

3. **Looker Studio ダッシュボード**
   - 全履歴を可視化

4. **統計的有意差判定**
   - DID分析 / CausalImpact で効果の統計的検証

---

以上でセットアップ完了です。質問があれば遠慮なくどうぞ！
