# Slack: #nonaka_test
> 取得日時: 2026/2/23 19:10:01  
> 対象期間: 直近3日分  
> メッセージ数: 4件（親: 4件 + スレッド返信）

---

**Rikito Nonaka/野中 力斗** (2026/2/21 9:28:10)


**Rikito Nonaka/野中 力斗** (2026/2/21 9:35:10)


**Rikito Nonaka/野中 力斗** (2026/2/23 16:10:52)
SEOの計測・分析・施策提案をMECEに自動化するSlack Botを作った話——既存ツールにない「全体最適」という視点
野中力斗（のなか りきと）です。
前回のnoteでは、Claude CodeとCursorを使ったSEO自動化システムの構築途中で直面した「AIの長期記憶問題」について書きました。MDファイルを中間生成物として介在させることで、精度の劣化を回避しながら開発を進めるという泥臭いアプローチの話です。
今回はその続編。あの開発がどこに着地したのか——具体的には、SEOの数値計測から分析、インサイト抽出、そしてネクストアクションの提案までをMECEに洗い出すSlack Botを完成させた話をします。このブログでは、具体的な機能やプロンプト設計、実装のアプローチについても紹介していきます。
なぜ作ったのか——「ネクストアクションの妥当性」を重視したかった
SEOツールは世の中に数多くある。Ahrefs、Semrush、SE Ranking、Screaming Frog。どれも個別の分析領域では優れた機能を持っていて、コンテンツ制作や内部・外部施策の妥当性検証、キーワードリサーチやサイト監査については十分な精度で実施できる。
しかし、SEO施策を俯瞰したときに、以下の2つの問いに自動で答えてくれるツールは、僕の知る限りほとんどなかった。
*1. いま、どこが最も重要度の高い問題なのか* *2. それを解決することで、どれくらいのインパクトが見込めるのか*
この2つは、SEO担当者が日々頭の中で行っている判断そのものだ。しかし、その判断は属人的で、経験則に依存しがちで、なおかつバイアスがかかりやすい。
DemandSageの調査によれば、AIを活用したSEOツールの導入率は2025年時点でB2B企業の58%、B2C企業の60%に達している。さらに86%のSEO担当者がすでにAIを何らかの形でワークフローに統合しているという。しかし、これらの多くは「部分最適」——キーワードリサーチの効率化、コンテンツ生成の高速化、技術SEOの監査自動化——にとどまっている。
僕が今回やりたかったのは、そうした部分最適の先にある「全体最適」。定量データを横断的に取得し、施策間の影響度を比較して、インパクトの大きい順にネクストアクションを提示する。人間がゼロベースで考えなくても、AIが構造的に分析して施策の幅出しまで行える仕組み。
これが、今回のSlack Bot制作の動機です。
参考にした先駆者たち——データ取得→分析→アクションの一気通貫フロー
今回の開発にあたって、既存のオープンソースプロジェクトを徹底的に調べた。自力でゼロから作り上げるのは難しいと前回のブログでも正直に書いたが、先駆者たちが公開している仕組みをうまく組み合わせることを主軸に据えている。
1. SEO Machine（TheCraigHewitt/seomachine）
データ収集→分析→インサイト→アクションの一連フローに最も近かったのが、このプロジェクトだ。Google Analytics 4、Google Search Console、DataForSEOとのデータ連携があり、`/research`→`/analyze-existing`→`/optimize`→`/performance-review`といったカスタムコマンドで一連のワークフローを回せる。
コンテンツ分析、SEOスコアリング（0〜100）、キーワード密度・クラスタリング、検索インテント検出などのエージェントも内蔵されており、WordPress REST API経由のパブリッシュまで対応している。数値データの取得→分析→ネクストアクション提示の流れが最も体系的に設計されていた。
2. claude-seo（AgriciDaniel/claude-seo）
技術SEO、オンページ分析、E-E-AT評価、スキーマ、GEO（AI検索最適化）まで、12のサブスキルと6つのサブエージェントで構成されている。`/seo audit`でサイト全体の監査、`/seo page`で個別ページ分析、`/seo geo`でAI検索最適化の分析が可能。インストールはワンライナーで完結する。
```curl -fsSL <https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/install.sh> | bash```
3. seo-geo-claude-skills（aaron-he-zhu）
20のSEO/GEOスキルと9つのコマンドを含み、キーワードリサーチ→競合分析→コンテンツギャップ分析→コンテンツ作成→GEO最適化→メタタグ/スキーマ→品質監査→パブリッシュ→ランキング追跡という完全なワークフローが定義されている。CORE-EEATとCITEフレームワークを使った品質監査が特徴で、スキル間のハンドオフ（前の分析結果を次のスキルに引き継ぐ）にも対応している。
4. claude-skills（alirezarezvani/claude-skills）
87以上のCLIユーティリティを含むモジュラー構成。SEO最適化、ブランドボイス分析、コンテンツカレンダーなどマーケティング全般をカバーしている。
MCP連携という鍵
上記のスキル系プロジェクトは、主にクロール・分析・レポートが中心だ。AhrefsのようなSEOツールから定量データを取得して分析に組み込むには、MCP（Model Context Protocol）やDataForSEO APIとの連携が必要になる。この点で、SEO Machineが最もデータ連携に力を入れている印象だった。
既存ツールの課題——「部分最適」と「全体最適」の壁
これらのプロジェクトはそれぞれ優れているが、共通する課題がある。
*個々の分析領域では最適化されているものの、「全体最適化」という視点が弱い。*
SEO Machineは確かに一気通貫フローとして最も体系的だった。しかし、DataForSEOベースの設計であり、日本語メディアでの運用を前提としたGSC・GA4・Ahrefs・Clarityの4ソース統合には対応していなかった。また、claude-seoやseo-geo-claude-skillsは分析の深さでは優秀だが、施策間のインパクト比較やROI指数の算出といった「優先度の定量化」は行わない。
たとえば、技術SEOの監査ツールがサイト内のエラーを検出する。コンテンツ分析ツールがキーワード密度の改善を提案する。競合分析ツールがコンテンツギャップを特定する。しかし、それらを横断して「いま最もインパクトの大きい施策は何か」を定量的に比較し、優先順位付けするところまで自動で行うツールは、驚くほど少ない。
SEO担当者の業務時間のうち、データ分析と解釈に費やされる時間はAIツールの導入により最大50%削減できるとされている。しかしこの効率化は、個別タスクの高速化によるもの。施策全体の優先度判断——どの施策に限られたリソースを集中投下すべきか——は、依然として人間の判断に委ねられている。
今回のBot開発では、この「全体から見たときに影響度の高い施策は何か」という幅出しを、AIに任せることを目指した。
完成したもの——Slack × Claude Code × 4データソースの統合Bot
概要
<http://jo-katsu.com|jo-katsu.com>（就活メディア）のSEO分析業務を、Slackのスラッシュコマンドから実行できるボットシステム。内部でClaude Code CLIを起動し、4つのデータソース（Google Search Console・GA4・Ahrefs・Clarity）からリアルタイムにデータを取得。分析から施策提案までを自動実行し、結果をSlackに投稿する。
技術スタックはこのとおり。
• ランタイム: Node.js 18+（ES Modules）
• Slack連携: @slack/bolt 4.1.0（Socket Mode）
• AI実行: Claude Code CLI（claude-sonnet-4-20250514）
• データソース: GSC（MCP）、GA4（Python CLI）、Ahrefs（MCP）、Clarity（MCP）
• プロセス管理: pm2 + pm2-windows-startup
• 動作環境: Windows 11 ローカルPC（クラウド不要）
9つのSlackコマンド
   コマンド 機能 所要時間     `/seo-cv [YYYY-MM]` CV指標レポート（会員登録・資料DL数の日別推移、月次目標達成率、CTAバナー効果測定） 2〜3分   `/seo-top100` オーガニックセッションTop100記事の前月比較 + 要対応記事の原因分析・対策提案 3〜5分   `/seo-weekly` 週次SEOパフォーマンスレポート（検索・順位・UX・競合の4軸分析） 2〜4分   `/seo-dashboard` 月次エグゼクティブダッシュボード（KPI達成度・施策ROI・次月優先施策） 3〜5分   `/seo-analytics [依頼内容]` 任意の分析依頼を自然言語で実行 2〜6分   `/seo-verify [対象]` 分析データの3重検証チェック（数値再計算・クロスチェック・信頼度スコア） 1〜2分   `/seo-measure evt-XXX` 変更のBefore/After効果測定 2〜3分   `/seo-log` CTA変更等をモーダルフォームで記録（ベースラインデータ自動取得） 1〜2分   `/seo-stop` 実行中の処理を即座に停止 即時   ポイントは、これらが単なるデータの取得・表示にとどまらないこと。各レポートには必ず「優先度付きのネクストアクション」が含まれる。
このBotが行う分析の具体例
*`/seo-top100`の場合:* GSCとGA4からTop100記事のセッション数を前月比較し、要対応記事を自動検出する。セッションが30%以上減少した記事、あるいは4週連続で下落している記事にはフラグが立つ。フラグが立った記事には、Ahrefs・Clarityと連携した原因分析が走り、競合ページの実際のURL・タイトル・H2構造まで提示される。
施策の優先度は*ROI指数*で定量化される。計算式はこうだ。
```ROI index = 期待月間クリック増 / 推定作業時間
期待効果 = impressions × (target CTR − current CTR)```
つまり、「この施策に○時間かけると、月間○クリックの増加が見込める」という形で、施策間の比較が可能になる。
*`/seo-dashboard`の場合:* CV指標レポート、オーガニックTop100レポート、週次SEOレポートの3つを統合し、KPI達成度・施策ROI・次月優先施策をサマリーする。施策の実現率が60%未満の場合は見積精度のレビューを自動推奨する仕組みもある。
もう一つ特徴的なのが、「何もしないリスク」の定量化だ。放置した場合にどれだけの機会損失が発生するかを数値で示す。「急いで対応すべき」というのは感覚ではなく、データに基づいた判断になる。
データの信頼性を担保する3重検証
分析の精度を担保するために、データ検証レイヤーを3段階で組み込んでいる。
1. *1次検証*: 数値再計算・範囲チェック・データ鮮度・サンプルサイズの検証
2. *2次検証*: ソース間のクロスチェック（GSC/GA4の整合性、Ahrefs順位データとGSC順位の一致度など）
3. *3次検証*: 信頼度スコアの算出（0〜100）
信頼度スコアが70未満の場合は、レポートに明示的な注意書きが入る。実際の運用では、Clarity対GA4でセッション数の不一致が検出され、データ信頼性スコアが67/100となったケースもあった。こうした透明性が、意思決定の質を支えてくれる。
なぜこのアプローチがすごいのか
人間がゼロベースで考える必要がない
従来のSEO施策では、データを見て→課題を特定して→優先度を判断して→アクションを考える、という一連のプロセスを人間が行っていた。ツールはあくまで各ステップの補助。
このBotでは、その一連のプロセスをAIが実行する。もちろん、完全な「自律」ではない。27個のカスタムコマンド仕様を定義し、データ取得の手順、分析のフレームワーク、出力のフォーマットまで詳細に設計している。AIが力を発揮するのは、その設計されたレールの上で、4つのデータソースを横断し、部分的な情報ではなく全体像を把握した上で施策を提案する部分だ。
一つの例を挙げよう。実際にjo-katsu.comで`/seo-top100`を実行した際、ある記事が前月比で約60.9%のセッション減少として検出された。Clarityのデータを見ると、その記事のJavaScriptエラー率が11.11%に達していた。つまり、ユーザーが記事にたどり着いても、技術的な問題でまともにコンテンツを閲覧できていない——これがセッション減の一因だった。
このインサイトは、GSCだけ見ていては絶対に出てこない。GA4だけでも出てこない。4つのデータソースを統合して、横断的に分析するからこそ導き出せるものだ。
施策の「幅出し」ができる
SEOの施策立案において、最も難しいのは「見落とし」を防ぐこと。人間はどうしても自分の経験則や直近の課題に引っ張られる。このBotは、MECE（Mutually Exclusive, Collectively Exhaustive）にデータを走査するから、人間が見落としがちな領域も漏れなくカバーする。
P0（緊急）、P1（来週確認→月次判断）、P2（中期施策）に優先度分けされたアクションリストが、コマンド一つで手に入る。
実装方法——どうやって作ったのか
アーキテクチャ
全体のデータフローはこうだ。
```Slack ユーザー
  | スラッシュコマンド（Socket Mode）
  v
Node.js (Slack Bolt) ← pm2で常駐
  | spawn (shell:false, windowsHide:true)
  | stdin経由でプロンプト送信
  v
Claude Code CLI
  | .claude/commands/*.md を参照して分析手順を自律実行
  | GSC (MCP) / GA4 (Python CLI) / Ahrefs (MCP) / Clarity (MCP)
  v
Markdown → Slack mrkdwn 変換 → 3000文字で分割投稿```
重要な設計判断がいくつかある。
*stdin経由でのプロンプト送信。* `-p`フラグではなくstdin経由で送る。これにより、シェルエスケープの問題を完全に回避した。
*`shell: false` + `windowsHide: true`。* Windows環境固有の問題として、`shell: true`でcmd.exe経由のspawnを行うと、Ctrl+Cシグナルがclaude.exeに伝播して異常終了する。orphaned claude.exeプロセスが12個残存して合計約1.6GBのメモリを消費するという事態も発生した。直接spawnに切り替えることで解決した。
*Socket Mode。* WebhookのURL公開が不要で、ファイアウォール内からそのまま動作する。クラウドへのデプロイが不要という手軽さも大きい。
プロンプト設計——品質を担保するための仕組み
全レポートに「根拠明記ルール」を組み込んでいる。
• 分析・判断・提案には必ず「定量データ（ツール名+数値）」または「参照ソースURL」を付記すること
• 要対応記事には競合ページの実際のURL・タイトル・H2構成を必須とすること
• 根拠なし・URL未記載の提案は禁止
• Good/Bad例 + 出力前チェックリストを仕様に組み込むこと
Claude Code CLIに対して27個のカスタムコマンド仕様（`.claude/commands/*.md`）を定義し、各コマンドの分析手順を詳細に記述している。前回のブログで紹介した「MDファイルでAIの長期記憶を補う」手法が、ここで活きている。
開発で乗り越えた技術課題
   課題 解決策     Windowsシグナル伝播（orphanedプロセス） `shell: false` + `windowsHide: true`でclaude.exe直接spawn   Slackメッセージ長制限 `MAX_SLACK_LENGTH`を3000に設定 + スレッド分割投稿   Claude CLI出力制御 「出力ルール」プロンプト（全文必須・サマリーのみ不可）   ネストセッション検出 `CLAUDECODE`環境変数を削除   レポート品質 エビデンス必須ルール + Good/Bad例 + 出力前チェックリスト   AI時代のSEOに求められる視点
Market.usの調査によると、AI搭載SEOソフトウェア市場は2025年の約39.8億ドルから、2035年には約326億ドルに達すると予測されている（CAGR 23.4%）。市場は急成長している。
しかし、市場の拡大＝課題の解決ではない。
AI Overviewの影響で自然検索からの流入が減少したと回答した企業は約6割に上るとされている。CTRは最大34.5%減少したという調査もある。検索の前提そのものが変わりつつある中で、「どのキーワードで何位を取るか」だけを追いかけるSEOは限界を迎えている。
だからこそ、施策の優先度を定量的に判断し、限られたリソースを最もインパクトの大きい領域に集中投下する——この「全体最適」の視点が、今まで以上に重要になる。
僕が今回作ったBotは、その視点を自動化する試みだ。
まとめ
今回、SEOの計測・分析・施策提案を一気通貫で自動化するSlack Botを作った。
既存のツールは個別領域では十分に優秀だが、「全体を俯瞰して、いまどの施策にリソースを投下すべきか」を定量的に判断するところまでは手が届いていなかった。このBotは、4つのデータソース（GSC・GA4・Ahrefs・Clarity）を横断し、AIが自律的にデータを取得→検証→分析→施策提案（優先度・ROI指数付き）を実行する。人間がゼロベースで考える部分を、構造的にAIへ委ねられる。
非エンジニアの僕がここまでたどり着けたのは、先駆者たちのオープンソースプロジェクトのおかげだ。ゼロベースでの開発が難しいなら、すでに公開されているものをうまく組み合わせればいい。前回のブログで紹介したMDファイル手法も、今回のプロンプト設計で大きく活きた。
次のnoteでは、このBotの出力するレポートの実例——実際のSlackスクリーンショットや、分析結果の詳細——をお見せする予定です。
まったりとした更新になりますが、引き続きよろしくお願いします。

参考
AI搭載SEOソフトウェア市場規模（2025年39.8億ドル→2035年326億ドル、CAGR 23.4%）: <http://Market.us|Market.us><https://market.us/report/ai-powered-seo-software-market/| — AI-powered SEO Software Market Size>
SEO担当者の86%がAIをワークフローに統合、B2Bの58%・B2Cの60%がAI SEOツールを導入: <https://www.demandsage.com/ai-seo-statistics/|DemandSage — 61 AI SEO Statistics 2026>
AIツール導入によりデータ分析時間が最大50%削減: <https://www.demandsage.com/ai-seo-statistics/|DemandSage — 61 AI SEO Statistics 2026>
AI SEOツール導入後、検索順位が6ヶ月以内に30%改善: <https://www.demandsage.com/ai-seo-statistics/|DemandSage — 61 AI SEO Statistics 2026>
AI Overviewの影響で自然検索流入が減少した企業は約6割: <https://www.extage-marketing.co.jp/web-school/ai-seo/|EXTAGE — AI時代のSEO施策10選>
AI OverviewによるCTR最大34.5%減少: <https://seomator.com/blog/ai-seo-statistics|SEOmator — 30+ AI SEO Statistics for 2026>
SEO Machine（TheCraigHewitt/seomachine）: <https://github.com/TheCraigHewitt/seomachine|GitHub — seomachine>
claude-seo（AgriciDaniel/claude-seo）: <https://github.com/AgriciDaniel/claude-seo|GitHub — claude-seo>
claude-skills（alirezarezvani/claude-skills）: <https://github.com/alirezarezvani/claude-skills|GitHub — claude-skills>
Claude Code + SE Ranking MCP連携: <https://seranking.com/webinars/claude-code-for-seo.html|SE Ranking — Claude Code for SEO>
Technical SEO MCP Server: <https://technicalseomcp.com/|Technical SEO MCP>
Claude Code Sub-Agents for Marketing: <https://www.digitalapplied.com/blog/claude-code-subagents-digital-marketing-guide|Digital Applied — Claude Code Subagents Guide>
• 前回のnote: <https://claude.ai/local_sessions/%E2%80%BB%E5%85%AC%E9%96%8B%E5%BE%8C%E3%81%ABURL%E3%82%92%E6%8C%BF%E5%85%A5|AIとのラリーを重ねるほど設計が崩れる——文系マーケターが試している対策>


**Slackbot** (2026/2/23 16:10:55)
<https://www.notion.so/malnainc/8557b99b61f54e0cbf837ebd5a804890>
