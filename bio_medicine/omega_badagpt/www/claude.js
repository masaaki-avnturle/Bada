/* ============================================================================
 *  claude.js — Anthropic Claude API 連携 (任意 / オプション)
 *  ユーザが自分の API キーを入力した場合のみ呼び出す。ブラウザ直呼び出しには
 *  anthropic-dangerous-direct-browser-access ヘッダを付与する。
 *  API キーは端末の localStorage にのみ保存され、外部送信は Anthropic のみ。
 * ==========================================================================*/
"use strict";

const ClaudeAPI = (() => {
  const ENDPOINT = "https://api.anthropic.com/v1/messages";

  async function complete({ apiKey, model, system, user, maxTokens = 2048 }) {
    if (!apiKey) throw new Error("APIキーが未入力です / API key missing");
    const body = {
      model: model || "claude-sonnet-4-5",
      max_tokens: maxTokens,
      system: system || "",
      messages: [{ role: "user", content: user }]
    };
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true"
      },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      let msg = "HTTP " + res.status;
      try { const j = await res.json(); msg = (j.error && j.error.message) || msg; } catch (e) {}
      throw new Error("Claude API: " + msg);
    }
    const data = await res.json();
    const text = (data.content || []).filter(c => c.type === "text").map(c => c.text).join("\n");
    return { text, usage: data.usage || null, model: data.model || body.model };
  }

  return { complete, ENDPOINT };
})();

if (typeof module !== "undefined" && module.exports) module.exports = ClaudeAPI;
