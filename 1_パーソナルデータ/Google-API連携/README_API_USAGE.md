# GA4・GSC API連携 実装完了報告

Google Analytics 4 (GA4) と Google Search Console (GSC) のAPI連携実装が完了し、正常にデータが取得できることを確認しました。

## 実施内容

1. **サービスアカウントキーの更新**
   - 新しいサービスアカウント `jo-katsu-com@feisty-gasket-487202-k7.iam.gserviceaccount.com` のキーファイルを適用しました。
   - ファイル配置: `nonaka/データ/feisty-gasket-487202-k7-992b8b630483.json`

2. **データ取得スクリプトの修正**
   - `nonaka/データ/google-analytics.js` と `google-search-console.js` のデフォルトキーパスを新しいキーファイルに変更しました。
   - これにより、`--key` オプションなしで実行可能になりました。

3. **動作確認**
   - GA4 (プロパティ: 356839446) からのデータ取得に成功。
   - GSC (サイト: https://jo-katsu.com/campus/) からのデータ取得に成功。

## 使い方

以下のコマンドでデータを取得できます。

### GA4 データ取得
```powershell
node "nonaka/データ/google-analytics.js" --property 356839446 --start 2026-02-01 --end 2026-02-14
```
オプション例:
- `--limit 10`: 10行だけ取得
- `--output csv`: CSV形式で出力

### GSC データ取得
```powershell
node "nonaka/データ/google-search-console.js" --site https://jo-katsu.com/campus/ --start 2026-02-01 --end 2026-02-14
```
オプション例:
- `--dimensions query,page`: クエリとページ毎に集計
- `--filter-query "就活"`: "就活"を含むクエリでフィルタ

## 注意事項

- キーファイルには重要な認証情報が含まれています。外部へ流出しないようご注意ください。
- 今回設定したサービスアカウント `jo-katsu-com@...` に権限が付与されているプロパティ/サイトのみデータ取得が可能です。
