import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

const SEO_MACHINE_DIR = process.env.SEO_MACHINE_DIR || 'C:/Users/your-user/Projects/seo-machine';
const CLAUDE_MODEL = process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514';
const PROGRESS_INTERVAL = 5000;
const MAX_TIMEOUT = 600000; // 10分

let activeProcess = null;

const LOG_FILE = path.join(SEO_MACHINE_DIR, 'slack-bot', 'bot.log');

function log(type, content) {
  const timestamp = new Date().toISOString();
  try {
    fs.appendFileSync(LOG_FILE, `[${timestamp}] [${type}] ${content}\n`);
  } catch (e) { /* ignore */ }
  console.log(`[${type}] ${content}`);
}

export function isProcessRunning() {
  return activeProcess !== null;
}

export function stopCurrentProcess() {
  if (!activeProcess) return false;
  try {
    activeProcess.kill('SIGTERM');
    const proc = activeProcess;
    setTimeout(() => {
      try { if (proc && !proc.killed) proc.kill('SIGKILL'); } catch (e) { /* already dead */ }
    }, 2000);
    activeProcess = null;
    log('INFO', '処理を停止しました');
    return true;
  } catch (e) {
    log('ERROR', `停止エラー: ${e.message}`);
    return false;
  }
}

/**
 * Claude CLIを実行し、結果を返す
 * @param {string} prompt
 * @param {object} callbacks
 * @param {Function} callbacks.onProgress - async (text) => void  進捗更新
 * @param {Function} callbacks.onError - async (text) => void  エラー通知
 * @returns {Promise<string|null>} 出力テキスト or null
 */
export async function runClaude(prompt, { onProgress, onError }) {
  if (activeProcess) {
    await onError('現在別のリクエストを処理中です。`/seo-stop` で中断できます。');
    return null;
  }

  // -p を使わず stdin でプロンプトを渡す（シェルエスケープ問題を回避）
  const args = [
    '--output-format', 'text',
    '--model', CLAUDE_MODEL,
    '--dangerously-skip-permissions',
  ];

  log('CLI', `実行: claude --model ${CLAUDE_MODEL} (prompt: ${prompt.substring(0, 80)}...)`);

  let outputBuffer = '';
  let lastSentLength = 0;
  let streamTimer = null;
  let isComplete = false;
  let timeoutTimer = null;

  return new Promise((resolve) => {
    // CLAUDECODE を除外してネストセッション検出を回避
    const cleanEnv = { ...process.env, FORCE_COLOR: '0' };
    delete cleanEnv.CLAUDECODE;

    // shell: false + windowsHide でコンソールシグナル伝播を防止
    const proc = spawn('claude.exe', args, {
      cwd: SEO_MACHINE_DIR,
      shell: false,
      env: cleanEnv,
      windowsHide: true,
    });
    activeProcess = proc;

    // stdin でプロンプトを送信して閉じる
    proc.stdin.write(prompt);
    proc.stdin.end();

    proc.stdout.on('data', (data) => {
      outputBuffer += data.toString();
    });

    proc.stderr.on('data', (data) => {
      const errText = data.toString();
      if (/[⠀-⣿]/.test(errText)) return; // スピナー文字フィルタ
      log('STDERR', errText.trim());
    });

    // 5秒間隔で進捗更新
    streamTimer = setInterval(async () => {
      if (isComplete) return;
      if (outputBuffer.length > lastSentLength && outputBuffer.length > 50) {
        try {
          const tail = outputBuffer.length > 2000
            ? outputBuffer.substring(outputBuffer.length - 2000)
            : outputBuffer;
          await onProgress(`処理中（${outputBuffer.length}文字出力済み）...\n\`\`\`\n${tail}\n\`\`\``);
          lastSentLength = outputBuffer.length;
        } catch (e) { /* rate limit */ }
      }
    }, PROGRESS_INTERVAL);

    // タイムアウト
    timeoutTimer = setTimeout(() => {
      if (!isComplete) {
        isComplete = true;
        clearInterval(streamTimer);
        stopCurrentProcess();
        onError(`タイムアウト（${MAX_TIMEOUT / 60000}分）で処理を中断しました。`);
        resolve(null);
      }
    }, MAX_TIMEOUT);

    proc.on('close', async (exitCode) => {
      if (isComplete) return;
      isComplete = true;
      clearInterval(streamTimer);
      clearTimeout(timeoutTimer);
      activeProcess = null;

      if (exitCode !== 0) {
        const errMsg = outputBuffer || '(出力なし)';
        log('ERROR', `Exit code: ${exitCode}`);
        await onError(`エラーで終了しました (code: ${exitCode})\n\`\`\`\n${errMsg.substring(0, 3800)}\n\`\`\``);
        resolve(null);
        return;
      }

      if (!outputBuffer.trim()) {
        log('INFO', '完了（出力なし）');
        resolve('');
        return;
      }

      log('SUCCESS', `完了: ${outputBuffer.length}文字`);
      resolve(outputBuffer);
    });

    proc.on('error', async (error) => {
      if (isComplete) return;
      isComplete = true;
      clearInterval(streamTimer);
      clearTimeout(timeoutTimer);
      activeProcess = null;
      log('ERROR', `実行エラー: ${error.message}`);
      await onError(`実行エラー: ${error.message}`);
      resolve(null);
    });
  });
}
