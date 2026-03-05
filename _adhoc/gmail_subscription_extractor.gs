/**
 * Gmail サブスクリプション自動抽出 → スプレッドシート自動書き込みスクリプト
 *
 * 概要:
 *   各ユーザーのGmailから請求・サブスク関連メールを検索し、
 *   Claude APIで構造化データに変換、既存の「最新_月定額コスト管理リスト」に
 *   直接書き込む。Slackワークフロー経由の自動申請も選択可能。
 *
 * Slackワークフロー「サブスクの新規契約更新」フォーム項目（12フィールド）:
 *   1.  サービス名              … テキスト
 *   2.  決済に使用したクレカ      … ドロップダウン（MFクレカ / Amex / アメックス / MF）
 *   3.  契約目的                … テキスト
 *   4.  支払いサイクル            … ドロップダウン（年 / 月）
 *   5.  アカウント数             … テキスト
 *   6.  月契約の理由 (任意)       … テキスト（月契約の場合のみ）
 *   7.  単価                    … テキスト（一回に支払う金額）
 *   8.  費用                    … テキスト（年間の費用）
 *   9.  担当者                  … ドロップダウン（社員名）
 *   10. 契約開始日               … 日付
 *   11. 契約更新日               … 日付
 *   12. 申し送り事項 (任意)       … テキスト
 *
 * セットアップ:
 *   1. Google Apps Script エディタ（script.google.com）で新規プロジェクト作成
 *   2. このコードを貼り付け
 *   3. 「プロジェクトの設定」→「スクリプトプロパティ」に以下を設定:
 *      - CLAUDE_API_KEY: Anthropic APIキー
 *      - SLACK_WEBHOOK_URL: （Slack Webhook使用時のみ）
 *      - SLACK_NOTIFY_WEBHOOK: （Slack通知を使用する場合のみ）
 *   4. previewSearch → testSingleExtraction の順でテスト
 *   5. トリガー設定で月次の自動実行を設定
 */

// ============================================================
// 設定
// ============================================================
function getConfig() {
  const props = PropertiesService.getScriptProperties();
  return {
    // Claude API（スクリプトプロパティから取得）
    CLAUDE_API_KEY: props.getProperty('CLAUDE_API_KEY') || '',
    CLAUDE_MODEL: 'claude-sonnet-4-6',

    // Slack Webhook（スクリプトプロパティから取得）
    SLACK_WEBHOOK_URL: props.getProperty('SLACK_WEBHOOK_URL') || '',
    SLACK_NOTIFY_WEBHOOK: props.getProperty('SLACK_NOTIFY_WEBHOOK') || '',

    // Google Spreadsheet
    SPREADSHEET_ID: '1Cs2CGarb59_VNmwc42uGU4yk6teEJKhBYADuHR8FnhI',
    SHEET_NAME: '最新_月定額コスト管理リスト',

    // 出力モード: 'slack_workflow' or 'direct_spreadsheet'
    OUTPUT_MODE: 'direct_spreadsheet',

    // Gmail検索設定
    SEARCH_DAYS: 30,        // 過去N日分のメールを検索（月次実行を想定）
    MAX_PROCESS: 25,        // 1回の実行で処理する最大スレッド数（GAS 6分制限対策）

    // 処理済みラベル名（再処理防止用）
    PROCESSED_LABEL: '_subscrip_processed',
  };
}


// ============================================================
// ドロップダウン選択肢の定義（Slackフォームの選択肢と完全一致させる）
// ============================================================

// 「決済に使用したクレカ」の有効な選択肢
const VALID_CARD_TYPES = ['MFクレカ', 'Amex', 'アメックス', 'MF'];

// 「支払いサイクル」の有効な選択肢
const VALID_PAYMENT_CYCLES = ['年', '月'];

// 「担当者」の有効な選択肢（社員 + 主要業務委託メンバー）
const VALID_PERSONS = [
  '高橋', '甲斐', '右田', '青砥', '神田', '安間',
  '永島', '古西', '吉成', '戸澤', '尾形', '内藤',
  '藤原', '野中',
  // 業務委託（スプレッドシートに担当者として頻出）
  '福原', '一法師', '中西',
];

// メールアドレス → 担当者名のマッピング
const EMAIL_TO_PERSON = {
  'kazuyuki.takahashi': '高橋',
  'seiji.kai':          '甲斐',
  'masahiro.kanda':     '神田',
  'rikito.nonaka':      '野中',
  'sho.fujiwara':       '藤原',
  'shuhei.nagashima':   '永島',
  // 業務委託
  'fukuhara':           '福原',
};


// ============================================================
// Gmail検索キーワード
// ============================================================
const SEARCH_QUERIES = [
  'subject:(請求書 OR 請求のお知らせ OR ご請求)',
  'subject:(invoice OR billing OR payment receipt)',
  'subject:(お支払い OR 支払い完了 OR 決済完了)',
  'subject:(領収書 OR receipt)',
  'subject:(サブスクリプション OR subscription OR 更新のお知らせ)',
  'subject:(ご利用料金 OR 料金のお知らせ OR 月額 OR 年額)',
  'subject:(契約更新 OR renewal OR 自動更新)',
  'subject:(ご注文の確認 OR order confirmation)',
  'subject:(プラン OR plan charge)',
];


// ============================================================
// メイン関数（トリガーから呼び出し）
// ============================================================
function extractSubscriptions() {
  const CONFIG = getConfig();
  const log = [];
  log.push(`[${new Date().toISOString()}] 実行開始`);

  // APIキーチェック
  if (!CONFIG.CLAUDE_API_KEY) {
    log.push('エラー: CLAUDE_API_KEY がスクリプトプロパティに設定されていません');
    log.push('「プロジェクトの設定」→「スクリプトプロパティ」で設定してください');
    Logger.log(log.join('\n'));
    return;
  }

  // 処理済みラベルを取得（なければ作成）
  let processedLabel = GmailApp.getUserLabelByName(CONFIG.PROCESSED_LABEL);
  if (!processedLabel) {
    processedLabel = GmailApp.createLabel(CONFIG.PROCESSED_LABEL);
    log.push('処理済みラベルを作成しました');
  }

  // 日付フィルタ
  const afterDate = new Date();
  afterDate.setDate(afterDate.getDate() - CONFIG.SEARCH_DAYS);
  const dateFilter = ` after:${Utilities.formatDate(afterDate, 'Asia/Tokyo', 'yyyy/MM/dd')}`;
  const excludeLabel = ` -label:${CONFIG.PROCESSED_LABEL}`;

  // メール検索
  let allThreads = [];
  for (const query of SEARCH_QUERIES) {
    const fullQuery = query + dateFilter + excludeLabel;
    const threads = GmailApp.search(fullQuery, 0, 50);
    allThreads = allThreads.concat(threads);
  }

  // スレッドIDで重複排除
  const seen = new Set();
  const uniqueThreads = allThreads.filter(thread => {
    const id = thread.getId();
    if (seen.has(id)) return false;
    seen.add(id);
    return true;
  });

  // GAS 6分制限対策: 処理件数を制限
  const threadsToProcess = uniqueThreads.slice(0, CONFIG.MAX_PROCESS);
  log.push(`検索結果: ${uniqueThreads.length} スレッド（重複排除後）→ 今回処理: ${threadsToProcess.length} 件`);

  if (uniqueThreads.length > CONFIG.MAX_PROCESS) {
    log.push(`※ 残り ${uniqueThreads.length - CONFIG.MAX_PROCESS} 件は次回実行時に処理されます`);
  }

  if (threadsToProcess.length === 0) {
    log.push('処理対象のメールはありませんでした');
    Logger.log(log.join('\n'));
    return;
  }

  // 各メールを処理
  const results = [];
  const errors = [];

  for (const thread of threadsToProcess) {
    const messages = thread.getMessages();
    const message = messages[messages.length - 1];

    try {
      const extracted = callClaudeAPI(message, CONFIG);

      if (extracted && extracted.relevant !== false) {
        // ドロップダウン値のバリデーション・正規化
        extracted.payment_cycle = normalizeDropdown(extracted.payment_cycle, VALID_PAYMENT_CYCLES);
        extracted.card_type = normalizeDropdown(extracted.card_type, VALID_CARD_TYPES);
        extracted.person = normalizeDropdown(extracted.person, VALID_PERSONS);

        // 担当者がnullの場合、メール宛先から推定
        if (!extracted.person) {
          extracted.person = resolvePersonFromEmail(message.getTo());
        }

        extracted._messageId = message.getId();
        extracted._subject = message.getSubject();
        extracted._from = message.getFrom();
        extracted._date = message.getDate().toISOString();
        results.push(extracted);
        log.push(`✓ 抽出成功: ${message.getSubject()}`);
      } else {
        log.push(`- スキップ（非関連）: ${message.getSubject()}`);
      }

      // 処理済みラベルを付与
      thread.addLabel(processedLabel);

    } catch (e) {
      errors.push({ subject: message.getSubject(), error: e.message });
      log.push(`✗ エラー: ${message.getSubject()} - ${e.message}`);
      // エラーでも処理済みラベルを付与（無限リトライ防止）
      thread.addLabel(processedLabel);
    }

    // API レートリミット対策
    Utilities.sleep(1000);
  }

  log.push(`\n抽出結果: ${results.length} 件成功 / ${errors.length} 件エラー`);

  // 出力
  if (results.length > 0) {
    if (CONFIG.OUTPUT_MODE === 'slack_workflow') {
      outputToSlackWorkflow(results, log, CONFIG);
    } else {
      outputToSpreadsheet(results, log, CONFIG);
    }
  }

  Logger.log(log.join('\n'));
}


// ============================================================
// Claude API 呼び出し（Slackフォームの12フィールドに完全対応）
// ============================================================
function callClaudeAPI(message, CONFIG) {
  const subject = message.getSubject();
  const from = message.getFrom();
  const date = message.getDate();
  const to = message.getTo();

  // 本文取得（プレーンテキスト優先、HTMLフォールバック）
  let body = message.getPlainBody();
  if (!body || !body.trim()) {
    body = message.getBody().replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  }
  const truncatedBody = (body && body.trim()) ? body.substring(0, 4000) : '（本文なし）';

  const prompt = `以下のメールから、サブスクリプション・契約・請求に関する情報を抽出してください。
Slackワークフロー「サブスクの新規契約更新」フォームの12項目に合わせたJSONで返答してください。

## 抽出項目（JSON形式で返答）

{
  "relevant": true,
  "service_name": "サービス名（正式名称。例: Slack, Google Workspace, Ahrefs）",
  "card_type": "決済に使用したクレカ。以下の選択肢のいずれか: MFクレカ / Amex / アメックス / MF。不明ならnull",
  "purpose": "契約目的（業務効率化, クリエイティブ制作, 競合分析, 労務関連, ログイン情報管理, 受付業務 等。不明ならnull）",
  "payment_cycle": "支払いサイクル。「年」または「月」のいずれか。年一回なら「年」、毎月なら「月」。不明ならnull",
  "account_count": "アカウント数（数値。不明なら1）",
  "monthly_reason": "月で契約した人は年単位での契約をしない理由（payment_cycleが「月」の場合のみ。年契約の選択肢がない、試用中、等。不明ならnull）",
  "unit_price": "単価（一回に支払う金額。税込円表記。例: ¥3,100。USDの場合は $20 のように記載）",
  "cost": "費用（年間の費用。年契約ならunit_priceと同額、月契約ならunit_price×12。例: ¥37,200）",
  "person": "担当者（メール宛先から推測する姓のみ。以下の選択肢: 高橋/甲斐/右田/青砥/神田/安間/永島/古西/吉成/戸澤/尾形/内藤/藤原/野中/福原。不明ならnull）",
  "contract_start_date": "契約開始日（YYYY-MM-DD形式。不明ならnull）",
  "renewal_date": "契約更新日（YYYY-MM-DD形式。次回更新日・次回請求日があればそれを記入。不明ならnull）",
  "notes": "申し送り事項（特記事項。プラン名、通貨換算メモ、注意点など。なければnull）",
  "status": "契約状況。「契約中」「解約済み」「解約手続き中」のいずれか。請求・更新メールなら「契約中」、解約確認メールなら「解約済み」。不明なら「契約中」"
}

## ルール
- 請求・サブスクリプション・契約に関連しないメールは {"relevant": false} のみ返す
- 金額は日本円表記を優先。USDの場合は「$20」のように原文通り記載し、備考に「1ドル=約XXX円で約¥X,XXX」と換算メモを添える
- 「費用」は年間コストを記入する（月額の場合は×12で算出）
- ドロップダウン項目（card_type, payment_cycle, person）は必ず指定した選択肢の中から選ぶ。該当なしならnull
- 不明な項目はnullとする
- JSONのみを返し、それ以外のテキストは含めない

## メール宛先 → 担当者マッピング（@malna.co.jp）
- kazuyuki.takahashi → 高橋
- seiji.kai → 甲斐
- masahiro.kanda → 神田
- rikito.nonaka → 野中
- sho.fujiwara → 藤原
- shuhei.nagashima → 永島
- fukuhara → 福原
- contact@malna.co.jp → null（共有アドレスのため担当者不明）

## メール情報
件名: ${subject}
送信者: ${from}
宛先: ${to}
日付: ${Utilities.formatDate(date, 'Asia/Tokyo', 'yyyy-MM-dd HH:mm')}

本文:
${truncatedBody}`;

  const payload = {
    model: CONFIG.CLAUDE_MODEL,
    max_tokens: 1024,
    messages: [{ role: 'user', content: prompt }],
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'x-api-key': CONFIG.CLAUDE_API_KEY,
      'anthropic-version': '2023-06-01',
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  };

  const response = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', options);
  const statusCode = response.getResponseCode();

  if (statusCode !== 200) {
    throw new Error(`Claude API error (${statusCode}): ${response.getContentText().substring(0, 300)}`);
  }

  const result = JSON.parse(response.getContentText());

  // レスポンス構造チェック
  if (!result.content || result.content.length === 0 || !result.content[0].text) {
    throw new Error(`Claude APIの応答にcontentがありません: stop_reason=${result.stop_reason}`);
  }

  const text = result.content[0].text;

  // JSON抽出（プレーンJSON → コードブロック → 貪欲マッチの順に試行）
  const trimmed = text.trim();
  let jsonStr;

  if (trimmed.startsWith('{')) {
    // プロンプト指示通りの純粋なJSON（最も一般的なケース）
    jsonStr = trimmed;
  } else {
    // コードブロック内のJSON
    const fenceMatch = text.match(/```json\s*([\s\S]*?)```/);
    if (fenceMatch) {
      jsonStr = fenceMatch[1].trim();
    } else {
      // フォールバック: 最初の { から末尾方向にパース試行
      const braceIdx = text.indexOf('{');
      if (braceIdx === -1) {
        throw new Error('Claude APIの応答からJSONを抽出できませんでした');
      }
      jsonStr = text.substring(braceIdx);
    }
  }

  try {
    return JSON.parse(jsonStr);
  } catch (e) {
    throw new Error(`JSONパース失敗: ${e.message}\n応答先頭200文字: ${text.substring(0, 200)}`);
  }
}


// ============================================================
// ドロップダウン値のバリデーション・正規化
// ============================================================
function normalizeDropdown(value, validOptions) {
  if (!value) return null;
  const trimmed = String(value).trim();

  // 完全一致
  if (validOptions.includes(trimmed)) return trimmed;

  // 大文字小文字を無視して一致
  const lower = trimmed.toLowerCase();
  const match = validOptions.find(opt => opt.toLowerCase() === lower);
  if (match) return match;

  // Amex ↔ アメックス の相互変換
  if (lower === 'amex' || lower === 'アメックス') {
    if (validOptions.includes('Amex')) return 'Amex';
    if (validOptions.includes('アメックス')) return 'アメックス';
  }

  return null;
}


// ============================================================
// メールアドレスから担当者名を解決
// ============================================================
function resolvePersonFromEmail(toAddress) {
  if (!toAddress) return null;
  const lower = toAddress.toLowerCase();

  for (const [emailPrefix, personName] of Object.entries(EMAIL_TO_PERSON)) {
    if (lower.includes(emailPrefix)) {
      return personName;
    }
  }
  return null;
}


// ============================================================
// 出力A: Slack Workflow Webhook（フォームの12フィールドに完全対応）
//
// Webhookトリガー作成時の変数定義:
//   変数名(key)          | 型       | 対応フォーム項目
//   ---------------------|----------|------------------
//   service_name         | string   | サービス名
//   card_type            | string   | 決済に使用したクレカ
//   purpose              | string   | 契約目的
//   payment_cycle        | string   | 支払いサイクル
//   account_count        | string   | アカウント数
//   monthly_reason       | string   | 月契約の理由（任意）
//   unit_price           | string   | 単価
//   cost                 | string   | 費用
//   person               | string   | 担当者
//   contract_start_date  | string   | 契約開始日
//   renewal_date         | string   | 契約更新日
//   notes                | string   | 申し送り事項（任意）
// ============================================================
function outputToSlackWorkflow(results, log, CONFIG) {
  let successCount = 0;

  for (const item of results) {
    const payload = {
      service_name:        item.service_name || '不明',
      card_type:           item.card_type || '',
      purpose:             item.purpose || '',
      payment_cycle:       item.payment_cycle || '',
      account_count:       String(item.account_count || 1),
      monthly_reason:      item.monthly_reason || '',
      unit_price:          item.unit_price || '',
      cost:                item.cost || '',
      person:              item.person || '',
      contract_start_date: item.contract_start_date || '',
      renewal_date:        item.renewal_date || '',
      notes:               item.notes || `[自動抽出] ${item._subject || ''}`,
    };

    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true,
    };

    const response = UrlFetchApp.fetch(CONFIG.SLACK_WEBHOOK_URL, options);
    const code = response.getResponseCode();

    if (code >= 200 && code < 300) {
      successCount++;
      log.push(`  → Slack送信OK: ${item.service_name}`);
    } else {
      log.push(`  ✗ Slack送信エラー: ${item.service_name} (HTTP ${code}) ${response.getContentText()}`);
    }

    Utilities.sleep(500);
  }

  log.push(`\nSlackワークフロー送信: ${successCount}/${results.length} 件成功`);
}


// ============================================================
// 出力B: Google Spreadsheet 直接書き込み（既存シート形式準拠）
// ============================================================
function outputToSpreadsheet(results, log, CONFIG) {
  const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);

  if (!sheet) {
    log.push(`エラー: シート「${CONFIG.SHEET_NAME}」が見つかりません`);
    return;
  }

  const lastRow = sheet.getLastRow();

  // 既存サービス名を取得（重複チェック用）
  const existingServices = new Set();
  if (lastRow > 1) {
    const serviceCol = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    serviceCol.forEach(row => {
      if (row[0]) existingServices.add(String(row[0]).trim().toLowerCase());
    });
  }

  let addedCount = 0;
  let skippedCount = 0;

  for (const item of results) {
    const serviceName = (item.service_name || '不明').trim();

    // 同名サービスが既に存在する場合はスキップ（重複防止）
    if (existingServices.has(serviceName.toLowerCase())) {
      log.push(`→ スキップ（既存）: ${serviceName}`);
      skippedCount++;
      continue;
    }

    // スプレッドシートの15列に合わせる
    const rowData = [
      serviceName,                                       // A: サービス名
      item.payment_cycle || '',                          // B: 支払いタイミング(年/月)
      item.card_type || '',                              // C: クレカ種別
      item.account_count || 1,                           // D: アカウント数
      item.purpose || '',                                // E: 契約目的
      item.unit_price || '',                             // F: 単価
      item.cost || '',                                   // G: 費用
      item.status || '契約中',                            // H: status
      item.person || '',                                 // I: 担当者
      item.contract_start_date || '',                    // J: 契約開始日
      item.renewal_date || '',                           // K: 契約更新日
      '',                                                // L: 支払いプラン変更前の想定コスト（空欄）
      '',                                                // M: アカウント数削減後の想定コスト（空欄）
      '',                                                // N: 削減可能なコスト（空欄）
      item.notes || `[自動抽出] ${item._subject || ''}`, // O: 備考
    ];

    sheet.appendRow(rowData);
    existingServices.add(serviceName.toLowerCase());
    addedCount++;
  }

  log.push(`スプレッドシート: ${addedCount} 件追加 / ${skippedCount} 件スキップ（既存）`);

  // Slack通知
  if (CONFIG.SLACK_NOTIFY_WEBHOOK) {
    const summary = results
      .map(r => `• ${r.service_name || '不明'} - ${r.cost || '?'} (${r.payment_cycle || '?'})`)
      .join('\n');

    UrlFetchApp.fetch(CONFIG.SLACK_NOTIFY_WEBHOOK, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({
        text: `サブスク情報を自動抽出しました\n追加: ${addedCount}件 / スキップ(既存): ${skippedCount}件\n\n${summary}\n\n<https://docs.google.com/spreadsheets/d/${CONFIG.SPREADSHEET_ID}|スプレッドシートを確認>`,
      }),
      muteHttpExceptions: true,
    });
  }
}


// ============================================================
// ユーティリティ: テスト・デバッグ用
// ============================================================

/**
 * 検索プレビュー（実際の送信はしない）
 */
function previewSearch() {
  const CONFIG = getConfig();
  const afterDate = new Date();
  afterDate.setDate(afterDate.getDate() - CONFIG.SEARCH_DAYS);
  const dateFilter = ` after:${Utilities.formatDate(afterDate, 'Asia/Tokyo', 'yyyy/MM/dd')}`;

  let allResults = [];
  for (const query of SEARCH_QUERIES) {
    const threads = GmailApp.search(query + dateFilter, 0, 10);
    for (const thread of threads) {
      const messages = thread.getMessages();
      const msg = messages[messages.length - 1];
      allResults.push({
        subject: msg.getSubject(),
        from: msg.getFrom(),
        to: msg.getTo(),
        date: msg.getDate(),
      });
    }
  }

  // 重複排除
  const seen = new Set();
  allResults = allResults.filter(r => {
    const key = r.subject + r.from;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  Logger.log(`=== 検索プレビュー（過去${CONFIG.SEARCH_DAYS}日間） ===`);
  Logger.log(`ヒット数: ${allResults.length} 件\n`);
  allResults.forEach((r, i) => {
    Logger.log(`${i + 1}. [${r.date.toLocaleDateString('ja-JP')}] ${r.subject}`);
    Logger.log(`   From: ${r.from}`);
    Logger.log(`   To:   ${r.to}\n`);
  });
}


/**
 * 1通だけテスト抽出（Claude APIの動作確認用）
 * Webhook送信はしない。抽出結果のみログに出力。
 */
function testSingleExtraction() {
  const CONFIG = getConfig();

  if (!CONFIG.CLAUDE_API_KEY) {
    Logger.log('エラー: CLAUDE_API_KEY がスクリプトプロパティに設定されていません');
    return;
  }

  const threads = GmailApp.search('subject:(請求 OR invoice OR お支払い)', 0, 1);
  if (threads.length === 0) {
    Logger.log('テスト対象のメールが見つかりません');
    return;
  }

  const messages = threads[0].getMessages();
  const message = messages[messages.length - 1];
  Logger.log(`=== テスト対象メール ===`);
  Logger.log(`件名: ${message.getSubject()}`);
  Logger.log(`送信者: ${message.getFrom()}`);
  Logger.log(`宛先: ${message.getTo()}`);
  Logger.log(`日付: ${message.getDate()}\n`);

  try {
    const result = callClaudeAPI(message, CONFIG);
    Logger.log('=== Claude抽出結果 ===');
    Logger.log(JSON.stringify(result, null, 2));

    if (result.relevant !== false) {
      Logger.log('\n=== バリデーション後（最終出力値） ===');
      Logger.log(`支払いサイクル: "${result.payment_cycle}" → "${normalizeDropdown(result.payment_cycle, VALID_PAYMENT_CYCLES) || '(null)'}"`);
      Logger.log(`クレカ種別:     "${result.card_type}" → "${normalizeDropdown(result.card_type, VALID_CARD_TYPES) || '(null)'}"`);
      Logger.log(`担当者:         "${result.person}" → "${normalizeDropdown(result.person, VALID_PERSONS) || resolvePersonFromEmail(message.getTo()) || '(null)'}"`);
    }
  } catch (e) {
    Logger.log(`エラー: ${e.message}`);
  }
}


/**
 * 処理済みラベルをリセット（再テスト用）
 * 500件超にも対応するバッチ処理版
 */
function resetProcessedLabel() {
  const CONFIG = getConfig();
  const label = GmailApp.getUserLabelByName(CONFIG.PROCESSED_LABEL);
  if (!label) {
    Logger.log('処理済みラベルが存在しません');
    return;
  }

  let total = 0;
  let threads;
  // 100件ずつバッチ処理（500件超対応）
  while ((threads = label.getThreads(0, 100)).length > 0) {
    for (const thread of threads) {
      thread.removeLabel(label);
    }
    total += threads.length;
  }
  Logger.log(`${total} スレッドからラベルを削除しました`);
}
