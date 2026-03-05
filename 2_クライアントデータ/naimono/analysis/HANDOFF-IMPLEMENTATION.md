# GA4/GSC バナー効果測定システム — 実装引き継ぎ書

**作成日**: 2026年2月21日
**目的**: 新しい Claude Code セッションがこの文書を読むだけで、現状の把握と次のアクションを実行できるようにする

---

## 1. プロジェクト概要

jo-katsu.com の CTA バナー差替え効果を Before/After で自動測定するシステム。
Google フォームに URL を入力 → GAS が Before データ取得 → 17日後に After データ取得 → 12指標で比較 → Slack に判定レポート送信。

---

## 2. 実装ステップの全体像と現在の進捗

| ステップ | 内容 | 所要時間 | 状態 |
|---------|------|---------|------|
| **Step 1** | Google フォーム + スプレッドシート作成 | 15分 | **未着手**（ユーザー作業） |
| **Step 2** | Slack Incoming Webhook URL 取得 | 10分 | **未着手**（ユーザー作業） |
| **Step 3** | Config.gs に本番値を設定 | 5分 | **未着手**（Step 1,2 の完了後） |
| **Step 4** | GAS デプロイ（コード転記 + Advanced Services + OAuth + トリガー） | 2時間 | **バグ修正が先に必要** |
| **Step 5** | 動作確認テスト | 30分 | **未着手** |
| **Step 6** | 初回本番運用 + 17日後レポート検証 | 17日 | **未着手** |

---

## 3. 各ステップの詳細

### Step 1: Google フォーム + スプレッドシート作成

**実施者**: ユーザー（rikitさん）

1. [Google Forms](https://docs.google.com/forms) で新規フォーム作成
2. タイトル: `バナー差替え記録フォーム`
3. 質問1: 「記事URL」（記述式、必須）
4. 質問2: 「変更内容」（記述式、任意）
5. フォーム「回答」タブ → スプレッドシートアイコン → 「新しいスプレッドシートを作成」
6. 開いたスプレッドシートの URL から **SPREADSHEET_ID** をメモ

```
URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
```

**成果物**: スプレッドシートID

---

### Step 2: Slack Incoming Webhook URL 取得

**実施者**: ユーザー（rikitさん）

1. [Slack API](https://api.slack.com/apps) → 「Create New App」 → 「From scratch」
2. App Name: `GA4 バナー効果測定`、ワークスペースを選択
3. 左メニュー「Incoming Webhooks」→ ON
4. 「Add New Webhook to Workspace」→ 通知チャンネルを選択 → 「許可する」
5. **Webhook URL** をコピー

```
形式: https://hooks.slack.com/services/T.../B.../...
```

**成果物**: Slack Webhook URL

---

### Step 3: Config.gs に本番値を設定

**実施者**: Claude Code（ユーザーから値を受領後）

Config.gs 内の以下4つのプレースホルダーを本番値に差し替える:

| 設定キー | 現在の値 | 置き換え先 |
|---------|---------|-----------|
| `GA4_PROPERTY_ID` | `'XXXXXXXXX'` | GA4 プロパティID（数字のみ） |
| `GSC_SITE_URL` | `'https://example.com/'` | `'https://jo-katsu.com/'` or `'sc-domain:jo-katsu.com'` |
| `SPREADSHEET_ID` | `'XXXX...XXX'` | Step 1 で取得した ID |
| `SLACK_WEBHOOK_URL` | `'https://hooks.slack.com/...'` | Step 2 で取得した URL |

**ファイル**: `C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\gas\Config.gs`

---

### Step 4: GAS デプロイ

**実施者**: ユーザー（手順は SETUP.md に記載）

1. スプレッドシートから「拡張機能」→「Apps Script」
2. 既存の「コード.gs」を削除
3. 7ファイルを作成して、ローカルの gas/ ディレクトリからコードを転記:
   - Config.gs, Main.gs, GA4.gs, GSC.gs, Sheet.gs, Slack.gs, Utils.gs
4. appsscript.json を上書き
5. Advanced Services 有効化（GA4 Data API v1beta + Search Console API v3）
6. OAuth 承認（testFormSubmit 関数を実行して権限付与）
7. トリガー設定（onFormSubmit をフォーム送信時に設定）

**前提条件**: **Step 4 の前に、後述のバグ修正が完了していること**

---

### Step 5: 動作確認テスト

**実施者**: ユーザー + Claude Code

1. `testFormSubmit()` を GAS エディタから手動実行
2. 確認項目:
   - スプレッドシートに「変更ログ」「データ」シートが自動作成されるか
   - Before データが記録されるか
   - Slack に検知通知が届くか
   - 時限トリガーが作成されるか
3. Google フォームから実際にテスト送信して同様に確認

---

### Step 6: 初回本番運用

**実施者**: ユーザー

1. 実際のバナー差替え後、Google フォームに URL を入力
2. 17日後に自動でレポートが Slack に届く
3. レポートの数値を GA4 管理画面と手動で照合（初回のみ推奨）
4. 判定（改善/悪化/変化なし）を確認し、ネクストアクションを判断

---

## 4. GAS コードのバグ — 懸念事項一覧

**コードレビュー実施日**: 2026年2月21日（前セッション）
**レビュー結果**: 8件の問題を発見、**すべて未修正**

### 致命的バグ（2件）— 修正しないとシステムがクラッシュする

#### Bug 1: Sheet.gs — scrollData の null 参照でクラッシュ

| 項目 | 内容 |
|------|------|
| **ファイル** | `Sheet.gs` 155〜158行目（`writeDataRecord()` 関数内） |
| **原因** | Main.gs が `scrollData: null` を渡している（61行目, 169行目）のに、Sheet.gs は `scrollData.scroll_25` のように直接アクセス |
| **影響** | フォーム送信時に TypeError で**全処理が停止** |
| **修正** | `scrollData?.scroll_25 \|\| 0` または `(scrollData && scrollData.scroll_25) \|\| 0` に変更（4箇所） |

```javascript
// 修正前（Sheet.gs 155〜158行目）
scrollData.scroll_25 || 0,
scrollData.scroll_50 || 0,
scrollData.scroll_75 || 0,
scrollData.scroll_90 || 0,

// 修正後
(scrollData && scrollData.scroll_25) || 0,
(scrollData && scrollData.scroll_50) || 0,
(scrollData && scrollData.scroll_75) || 0,
(scrollData && scrollData.scroll_90) || 0,
```

---

#### Bug 2: Slack.gs — scroll データの null 参照でクラッシュ

| 項目 | 内容 |
|------|------|
| **ファイル** | `Slack.gs` 125〜128行目（`sendSlackReport()` 関数内） |
| **原因** | `before.scroll.scroll_90` と `after.scroll.scroll_90` にアクセスしているが、scroll は null |
| **影響** | 17日後のレポート送信時に TypeError で**レポートが届かない** |
| **修正** | スクロール行を削除し、代わりに CV 数を表示 |

```javascript
// 修正前（Slack.gs 125〜128行目の fields 配列 4番目）
{
  type: 'mrkdwn',
  text: `*スクロール90%到達*\n${before.scroll.scroll_90} → ${after.scroll.scroll_90} (${changes.scroll_90})`
}

// 修正後: CV数に差し替え
{
  type: 'mrkdwn',
  text: `*CV数*\n${before.ga4.keyEvents} → ${after.ga4.keyEvents} (${changes.keyEvents})`
}
```

---

### 重要な問題（3件）— データの正確性に影響

#### Bug 3: GA4.gs — `conversions` メトリクス廃止（2024年5月6日〜）

| 項目 | 内容 |
|------|------|
| **ファイル** | GA4.gs 36行目、および関連5ファイル |
| **原因** | GA4 Data API で `conversions` は廃止され `keyEvents` に移行済み |
| **影響** | CV 数が取得できない（エラーまたは常に 0） |
| **修正** | `conversions` → `keyEvents` を以下のファイルで一括変更 |

**連鎖修正箇所**:

| ファイル | 行 | 修正内容 |
|---------|-----|---------|
| GA4.gs | 36行目 | `{ name: 'conversions' }` → `{ name: 'keyEvents' }` |
| GA4.gs | 81行目 | `conversions: parseFloat(...)` → `keyEvents: parseFloat(...)` |
| Config.gs | 50行目 | `conversions: 0.20` → `keyEvents: 0.20` |
| Utils.gs | 79行目 | `conversions: calculateChange(before.ga4.conversions, ...)` → `keyEvents: calculateChange(before.ga4.keyEvents, ...)` |
| Utils.gs | 124行目 | `conversions: safeChangeRate(before.ga4.conversions, ...)` → `keyEvents: safeChangeRate(before.ga4.keyEvents, ...)` |
| Sheet.gs | 154行目 | `ga4Data.conversions` → `ga4Data.keyEvents` |
| Sheet.gs | 201行目 | `conversions: row[11]` → `keyEvents: row[11]` |

---

#### Bug 4: GSC.gs — 画像検索フィルタの実装誤り

| 項目 | 内容 |
|------|------|
| **ファイル** | `GSC.gs` 67〜110行目（`fetchGSCImageSearchData()` 関数） |
| **原因** | `searchAppearance: 'IMAGE'` ディメンションフィルタを使用しているが、画像検索タイプの指定は `type: 'image'` をリクエストのトップレベルに置く |
| **影響** | 画像検索データが正しく取得できない（常に 0 件になる可能性） |
| **修正** | `searchAppearance` フィルタを削除し、`type: 'image'` をリクエストオブジェクトのトップレベルに追加 |

```javascript
// 修正後
const request = {
  startDate: formatDateYYYYMMDD(startDate),
  endDate: formatDateYYYYMMDD(endDate),
  dimensions: ['page'],
  type: 'image',  // ← ここに追加
  dimensionFilterGroups: [{
    filters: [{
      dimension: 'page',
      operator: 'equals',
      expression: pageUrl
    }]
    // searchAppearance フィルタは削除
  }],
  rowLimit: 1
};
```

---

#### Bug 5: Config.gs / Utils.gs — メトリクス名の不一致

| 項目 | 内容 |
|------|------|
| **ファイル** | Config.gs 45行目、Utils.gs 121行目 |
| **原因** | Config の `METRIC_WEIGHTS` では `avgEngagementTime` と定義、Utils.gs の `determineVerdict()` では `before.ga4.avgSessionDuration` を参照。キー名が不一致 |
| **影響** | 現状は偶然動くが、将来の変更で判定スコアが計算されなくなるリスク |
| **修正** | Config.gs と Utils.gs の両方を `avgSessionDuration` に統一 |

---

### 軽微な問題（3件）

#### Bug 6: Main.gs 241行目 — テスト URL がダミー

- `'https://example.com/campus/26469'` のまま
- テスト時に実際の URL に差し替えるコメントを追加

#### Bug 7: Utils.gs 182行目 — og:image の正規表現が片方向のみ

- `<meta property="og:image" content="...">` の順序のみマッチ
- `<meta content="..." property="og:image">` にマッチしない
- 両方の順序に対応する正規表現に修正

#### Bug 8: Config.gs 69〜72行目 — getConfig() がオブジェクト型を扱えない

- `PropertiesService` は文字列しか返さないが、`METRIC_WEIGHTS` はオブジェクト
- ScriptProperties に JSON 文字列で保存した場合、パースが必要
- `JSON.parse()` のフォールバックを追加

---

## 5. 推奨する作業順序

新しい Claude Code セッションで以下の順で作業を依頼する:

### Phase A: コード修正（Claude Code が実施）

```
1. 上記8件のバグをすべて修正
2. 修正後のコード全体の整合性を確認（特に conversions → keyEvents の統一）
```

### Phase B: 環境準備（ユーザーが実施）

```
3. Step 1: Google フォーム + スプレッドシート作成 → SPREADSHEET_ID を取得
4. Step 2: Slack Webhook URL を取得
5. 取得した2つの値を Claude Code に伝える
```

### Phase C: 本番値の設定（Claude Code が実施）

```
6. Step 3: Config.gs に本番値を設定（GA4_PROPERTY_ID, GSC_SITE_URL, SPREADSHEET_ID, SLACK_WEBHOOK_URL）
```

### Phase D: デプロイ（ユーザーが実施）

```
7. Step 4: GAS エディタでコードを転記、Advanced Services 有効化、OAuth承認
8. Step 5: testFormSubmit で動作確認
9. Step 6: トリガー設定 → 初回本番運用開始
```

---

## 6. ファイル配置

```
C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\
├── gas/
│   ├── Config.gs          ... 設定値（プレースホルダー状態）
│   ├── Main.gs            ... エントリーポイント（onFormSubmit, generateReport）
│   ├── GA4.gs             ... GA4 Data API 連携
│   ├── GSC.gs             ... Search Console API 連携
│   ├── Sheet.gs           ... スプレッドシート読み書き
│   ├── Slack.gs           ... Slack 通知
│   ├── Utils.gs           ... ユーティリティ関数
│   ├── appsscript.json    ... GAS マニフェスト
│   └── SETUP.md           ... セットアップガイド
├── HANDOFF-IMPLEMENTATION.md  ... 本ファイル（実装フロー + バグ一覧）
├── HANDOFF-GAS-BUGFIX.md     ... バグ修正のみの詳細引き継ぎ書（前回作成）
├── integration-review-final-report.md  ... Agent Teams 統合レビュー（466行）
└── ...（提案書等）

C:\Users\rikit\Projects\
└── GA4-GSC-measurement-system-complete-summary.md  ... 全体サマリー（712行）
```

---

## 7. 補足情報

### 確定済みの設計判断

- **計測方式**: Before/After 単純比較（対照群なし、外的要因は考慮しない）
- **計測期間**: Before 14日 + After 14日（GSC 遅延3日バッファ → 17日後にレポート）
- **判定指標**: 12指標の重み付きスコア（スクロール4指標は GTM 未設定のため除外）
- **判定閾値**: +5%以上で「改善」、-5%以下で「悪化」
- **レポート頻度**: 月4〜10回（バナー差替え頻度に依存）
- **BigQuery**: 不要（Google Sheets で対応）
- **Agent Teams**: 不要（人間が Slack レポートを判断）

### ユーザー情報

- **言語**: 日本語
- **技術レベル**: Claude Code を使えるが、プログラマーではない
- **プラットフォーム**: Windows 11
- **GA4/GTM 管理権限**: あり
- **GSC 権限**: 取得済み・連携完了
- **Slack チャンネル**: 決定済み

---

## 8. Claude Code への依頼文テンプレート

以下をコピーして新しいセッションで使用できる:

```
C:\Users\rikit\Projects\2_クライアントデータ\naimono\analysis\HANDOFF-IMPLEMENTATION.md を読んで、
セクション4に記載されている8件のバグをすべて修正してください。
修正後、全ファイルの整合性（特に conversions → keyEvents の統一）を確認してください。
```

---

**本文書は、前セッションでのコードレビュー結果と全体の実装計画を統合した引き継ぎ書です。**
