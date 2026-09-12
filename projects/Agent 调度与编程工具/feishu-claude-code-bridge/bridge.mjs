#!/usr/bin/env node
/**
 * Feishu <-> Claude Code Bridge
 *
 * Architecture:
 *   Feishu user -> Feishu Cloud <-WS-> bridge.mjs -> Claude Agent SDK -> Claude Code
 *
 * Features:
 * - WebSocket long-connection (no public IP needed)
 * - Full Claude Code session (file read/write, bash, etc.)
 * - Per-chat session persistence
 * - Group chat @mention filter
 * - Long message auto-split
 * - Thinking indicator
 */

import * as lark from '@larksuiteoapi/node-sdk';
import { query } from '@anthropic-ai/claude-agent-sdk';
import fs from 'node:fs';
import path from 'node:path';

// ─── Config ────────────────────────────────────────────────────────
const FEISHU_APP_ID = process.env.FEISHU_APP_ID;
const FEISHU_APP_SECRET = process.env.FEISHU_APP_SECRET;
const WORKDIR = process.env.WORKDIR || process.cwd();
const AUTO_APPROVE = process.env.AUTO_APPROVE === 'true';

if (!FEISHU_APP_ID || !FEISHU_APP_SECRET) {
  console.error('Missing FEISHU_APP_ID or FEISHU_APP_SECRET');
  process.exit(1);
}

// ─── Feishu Client ─────────────────────────────────────────────────
const feishuClient = new lark.Client({
  appId: FEISHU_APP_ID,
  appSecret: FEISHU_APP_SECRET,
  logLevel: lark.LoggerLevel.WARN,
});

// ─── Session Management ────────────────────────────────────────────
// Each chat gets a persistent Claude Code session
const sessions = new Map(); // chatId -> { sessionId, busy }

// ─── Dedup ─────────────────────────────────────────────────────────
const seen = new Set();
function isDup(msgId) {
  if (seen.has(msgId)) return true;
  seen.add(msgId);
  setTimeout(() => seen.delete(msgId), 60_000);
  return false;
}

// ─── Extract text from Feishu message ──────────────────────────────
function extractText(msgType, content) {
  try {
    const parsed = typeof content === 'string' ? JSON.parse(content) : content;
    if (msgType === 'text') return (parsed.text || '').replace(/@_user_\d+/g, '').trim();
    if (msgType === 'post') {
      const lines = [];
      for (const lang of Object.values(parsed)) {
        if (lang?.content) {
          for (const line of lang.content) {
            for (const el of line) {
              if (el.tag === 'text') lines.push(el.text);
              if (el.tag === 'a') lines.push(el.text || el.href);
            }
          }
        }
      }
      return lines.join(' ').trim();
    }
    return '';
  } catch {
    return String(content);
  }
}

// ─── Group chat filter ─────────────────────────────────────────────
const REQUEST_RE = /帮|请|分析|总结|翻译|解释|写|算|查|搜|告诉|回答|说说/;
function shouldRespond(text, chatType, isMentioned) {
  if (chatType === 'p2p') return true;
  if (isMentioned) return true;
  if (/[?？]$/.test(text.trim())) return true;
  if (REQUEST_RE.test(text)) return true;
  return false;
}

// ─── Reply helper ──────────────────────────────────────────────────
async function reply(messageId, text) {
  if (!text?.trim()) return;
  const MAX = 3800;
  const chunks = [];
  let rest = text;
  while (rest.length > MAX) {
    let cut = rest.lastIndexOf('\n', MAX);
    if (cut < MAX * 0.3) cut = MAX;
    chunks.push(rest.slice(0, cut));
    rest = rest.slice(cut);
  }
  chunks.push(rest);

  for (const chunk of chunks) {
    try {
      await feishuClient.im.message.reply({
        path: { message_id: messageId },
        data: { msg_type: 'text', content: JSON.stringify({ text: chunk }) },
      });
    } catch (err) {
      console.error('Reply error:', err.message);
    }
  }
}

// ─── Process message with Claude Code ──────────────────────────────
async function processMessage(chatId, messageId, userText) {
  const session = sessions.get(chatId) || { sessionId: null, busy: false };
  if (session.busy) {
    await reply(messageId, '上一条还在处理中，请稍等...');
    return;
  }
  session.busy = true;
  sessions.set(chatId, session);

  // Thinking indicator (send after 2s)
  const thinkTimer = setTimeout(async () => {
    try {
      await reply(messageId, '💭 思考中...');
    } catch {}
  }, 2000);

  try {
    const opts = {
      cwd: WORKDIR,
      permissionMode: AUTO_APPROVE ? 'bypassPermissions' : 'default',
      allowDangerouslySkipPermissions: AUTO_APPROVE,
      maxTurns: 20,
      thinking: { type: 'adaptive' },
    };

    // Resume existing session if available
    if (session.sessionId) {
      opts.resume = session.sessionId;
    }

    const q = query({ prompt: userText, options: opts });

    let resultText = '';
    let newSessionId = null;

    for await (const msg of q) {
      // Capture session ID for future resume
      if (msg.session_id && !newSessionId) {
        newSessionId = msg.session_id;
      }

      if (msg.type === 'assistant') {
        // Extract text from assistant message
        const textBlocks = msg.message?.content?.filter(b => b.type === 'text') || [];
        for (const block of textBlocks) {
          if (block.text) resultText += block.text;
        }
      }

      if (msg.type === 'result') {
        if (msg.subtype === 'success' && msg.result) {
          resultText = msg.result;
        } else if (msg.is_error && msg.errors?.length) {
          resultText = `Error: ${msg.errors.join(', ')}`;
        }
      }
    }

    // Update session
    if (newSessionId) {
      session.sessionId = newSessionId;
    }

    clearTimeout(thinkTimer);

    if (resultText) {
      await reply(messageId, resultText);
    } else {
      await reply(messageId, '(无回复内容)');
    }

    console.log(`✅ [${chatId}] ${userText.slice(0, 40)}... -> ${(resultText || '').slice(0, 40)}...`);
  } catch (err) {
    clearTimeout(thinkTimer);
    console.error('Claude error:', err);
    await reply(messageId, `⚠️ 出错了: ${err.message}`);
  } finally {
    session.busy = false;
  }
}

// ─── Event handler ─────────────────────────────────────────────────
const eventDispatcher = new lark.EventDispatcher({}).register({
  'im.message.receive_v1': async (data) => {
    const msg = data.message;
    if (!msg || isDup(msg.message_id)) return;

    const chatId = msg.chat_id;
    const chatType = msg.chat_type;
    const text = extractText(msg.message_type, msg.content);
    if (!text) return;

    const isMentioned = msg.mentions?.some(m => m.id?.app_id === FEISHU_APP_ID);
    if (!shouldRespond(text, chatType, isMentioned)) return;

    console.log(`📨 [${chatType}:${chatId}] ${text.slice(0, 80)}`);
    processMessage(chatId, msg.message_id, text);
  },
});

// ─── Start WebSocket ───────────────────────────────────────────────
const wsClient = new lark.WSClient({
  appId: FEISHU_APP_ID,
  appSecret: FEISHU_APP_SECRET,
  logLevel: lark.LoggerLevel.WARN,
});

console.log('🚀 Feishu-Claude Bridge');
console.log(`   App ID:       ${FEISHU_APP_ID}`);
console.log(`   Work Dir:     ${WORKDIR}`);
console.log(`   Auto Approve: ${AUTO_APPROVE}`);

await wsClient.start({ eventDispatcher });
console.log('✅ WebSocket connected, listening...');

// ─── Shutdown ──────────────────────────────────────────────────────
const shutdown = () => {
  console.log('\n👋 Shutting down...');
  process.exit(0);
};
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
