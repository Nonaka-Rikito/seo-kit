# /measure-change - 変更効果測定

記録済みの変更イベントに対してAfterデータを取得し、Before/After比較レポートを生成する。

## パラメータ

`$ARGUMENTS` にイベントIDを指定する（例: evt-001）

## 実行手順

1. `data/change_events/events.jsonl` から該当イベントを読み込み
2. `data/change_events/{event_id}_baseline.json` からベースラインデータを読み込み
3. mcp-gsc の `compare_search_periods` で Before/After 比較データを取得
   - Before期間: ベースラインの期間
   - After期間: 変更日から現在まで（最低14日間）
4. `data_sources/verification/data_verifier.py` で数値を独立検証
   - 変化率の再計算
   - 値の範囲チェック
   - サンプルサイズの確認
5. `data_sources/verification/cross_checker.py` でクロスチェック
   - GSC vs GA4の整合性
   - トレンド方向の一致確認
6. Clarityの蓄積データがあれば行動データの変化も確認
7. レポートを生成して `output/` に保存
8. `events.jsonl` のステータスを "measured" に更新

## 出力フォーマット

```
📊 変更効果測定レポート
━━━━━━━━━━━━━━━━━━━━

イベント: evt-XXX
対象URL: https://...
変更内容: ...
仮説: ...

## Before/After 比較

| 指標 | Before | After | 変化 | 変化率 |
|------|--------|-------|------|--------|
| クリック | XXX | XXX | +XX | +XX% |
| インプレッション | XXX | XXX | +XX | +XX% |
| 平均順位 | X.X | X.X | -X.X | 改善 |
| CTR | X.X% | X.X% | +X.X% | +XX% |

## 判定

✅ 仮説は支持されました / ❌ 仮説は支持されませんでした

## データ信頼度

信頼度スコア: XX/100
[OK] 変化率再計算: 一致
[OK] 範囲チェック: 正常
[OK] サンプルサイズ: 十分 (sessions=XXX)

## 推奨アクション

- ...
```
