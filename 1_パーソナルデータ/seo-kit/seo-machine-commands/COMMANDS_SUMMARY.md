# SEO Machine Slash Commands まとめ

このファイルは `seo-machine/.claude/commands/` にあるコマンド仕様（`.md`）を、用途別に見やすく整理した一覧です。

## 配置場所

- コマンド仕様本体: `c:/Users/your-user/Projects/seo-machine/.claude/commands/`
- Slack Bot 実装側: `c:/Users/your-user/Projects/seo-machine/slack-bot/commands/`

## 主要分析コマンド（Slack Bot連携）

- `/seo-cv` -> `cv-report.md`
- `/seo-top100` -> `organic-top100.md`
- `/seo-weekly` -> `weekly-report.md`
- `/seo-verify` -> `verify-data.md`
- `/seo-measure` -> `measure-change.md`
- `/seo-log` -> `log-change.md`
- `/seo-dashboard` -> `executive-dashboard.md`

補足:
- `/seo-analytics` は現在 `slack-bot/commands/seo-analytics.js` で実装済み。
- 必要なら `seo-analytics.md` をこのディレクトリに追加して、プロンプト仕様を外部化可能。

## コンテンツ制作系コマンド

- `article.md`
- `write.md`
- `rewrite.md`
- `optimize.md`
- `publish-draft.md`
- `scrub.md`
- `analyze-existing.md`

## リサーチ系コマンド

- `research.md`
- `research-topics.md`
- `research-trending.md`
- `research-performance.md`
- `research-serp.md`
- `research-gaps.md`
- `performance-review.md`
- `priorities.md`

## ランディングページ系コマンド

- `landing-research.md`
- `landing-write.md`
- `landing-competitor.md`
- `landing-audit.md`
- `landing-publish.md`

## 目的別の使い分け（目安）

- **月次/週次の定例分析**: `cv-report.md`, `weekly-report.md`, `organic-top100.md`, `executive-dashboard.md`
- **施策の記録と効果測定**: `log-change.md` -> `measure-change.md`
- **データの信頼性確認**: `verify-data.md`
- **記事制作/改善**: `write.md`, `rewrite.md`, `optimize.md`, `scrub.md`
- **探索的な深掘り分析**: `research-*.md`, `performance-review.md`, `priorities.md`

## クライアント共有文（新仕様）

以下のSEOレポート系コマンドは、通常レポートに加えて「クライアント共有文（固定文+可変値）」の生成手順を持つ。

- `cv-report.md`
- `weekly-report.md`
- `organic-top100.md`
- `executive-dashboard.md`
- `performance-review.md`

共通ルール:
- 指定の文構造（挨拶 -> 期待効果 -> Top5 -> スプレッドシート案内）を維持する
- 数値は各レポートの実データ（現状クリック、想定クリック、増分、増加率）で差し替える
- 出力は **Markdown保存 + ターミナル表示** の両方を必須とする
- 保存先は `output/*-client-brief-YYYY-MM-DD.md`（`performance-review` は `research/` 配下）

## 次の整備候補

- `seo-analytics.md` を新規作成し、`slack-bot/commands/seo-analytics.js` から参照する構成に統一
- 各コマンドに「入力」「出力」「所要時間」「依存データソース」を共通フォーマットで追記
