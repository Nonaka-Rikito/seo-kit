# /log-change - クリエイティブ変更記録

ユーザーからクリエイティブ変更の情報を収集し、変更イベントログに記録する。
記録と同時にBefore計測のベースラインデータを自動取得する。

## 収集する情報

ユーザーに以下を質問して収集する:
1. **変更した記事のURL** - 例: https://jo-katsu.com/campus/26469
2. **変更内容** - 例: CTAボタンの色を青から赤に変更
3. **変更の種類** - cta_banner / title / meta_description / content / image / layout
4. **変更の理由/仮説** - 例: 赤いCTAの方がクリック率が上がるという仮説

## 実行手順

1. ユーザーから上記情報を収集
2. `data/change_events/events.jsonl` にイベントを追記:
   ```json
   {"id": "evt-XXX", "date": "YYYY-MM-DD", "page": "URL", "type": "種類", "description": "内容", "hypothesis": "仮説", "status": "measuring"}
   ```
3. mcp-gsc の `get_search_analytics` を使って変更日の前14日間のデータを取得
4. ベースラインデータを `data/change_events/evt-XXX_baseline.json` に保存
5. 「14〜17日後に `/measure-change evt-XXX` を実行してください」とリマインダーを出力

## 出力フォーマット

```
✅ 変更イベントを記録しました

イベントID: evt-XXX
記録日: YYYY-MM-DD
対象URL: https://...
変更内容: ...
仮説: ...

📊 ベースラインデータ（変更前14日間）:
  クリック: XXX
  インプレッション: XXX
  平均順位: X.X
  CTR: X.X%

⏰ 効果測定のリマインダー:
  17日後に以下のコマンドを実行してください:
  /measure-change evt-XXX
```
