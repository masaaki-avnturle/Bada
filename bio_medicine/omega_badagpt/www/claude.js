/* ============================================================================
 *  claude.js — Anthropic Claude API 連携 (任意 / オプション)
 *  ユーザが自分の API キーを入力した場合のみ呼び出す。ブラウザ直呼び出しには
 *  anthropic-dangerous-direct-browser-access ヘッダを付与する。
 *  API キーは端末の localStorage にのみ保存され、外部送信は Anthropic のみ。
 *
 *  対応モデル (既定: Claude Fable 5):
 *    claude-fable-5   — 最上位。thinking は常時オン (パラメータ送信不要)
 *    claude-opus-5 / claude-sonnet-5 / claude-haiku-4-5
 *  Fable 5 / Opus 5 では安全分類器による拒否 (stop_reason: "refusal") に備え、
 *  サーバ側フォールバック fallbacks:"default" を既定で有効化する
 *  (beta: server-side-fallback-2026-07-01 — 拒否カテゴリに応じて代替モデルで再実行)。
 * ==========================================================================*/
"use strict";

const ClaudeAPI = (() => {
  const ENDPOINT = "https://api.anthropic.com/v1/messages";

  const DEFAULT_MODEL = "claude-fable-5";
  const MODELS = [
    "claude-fable-5",
    "claude-opus-5",
    "claude-sonnet-5",
    "claude-haiku-4-5"
  ];

  // サーバ側フォールバックを既定で付けるモデル (拒否時に自動で代替実行)
  function wantsFallback(model) {
    return model === "claude-fable-5" || model === "claude-opus-5";
  }

  async function complete({ apiKey, model, system, user, maxTokens = 2048 }) {
    if (!apiKey) throw new Error("APIキーが未入力です / API key missing");
    const m = (model || DEFAULT_MODEL).trim();
    const body = {
      model: m,
      max_tokens: maxTokens,
      system: system || "",
      messages: [{ role: "user", content: user }]
    };
    const headers = {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true"
    };
    if (wantsFallback(m)) {
      body.fallbacks = "default";
      headers["anthropic-beta"] = "server-side-fallback-2026-07-01";
    }

    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers,
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      let msg = "HTTP " + res.status;
      try { const j = await res.json(); msg = (j.error && j.error.message) || msg; } catch (e) {}
      throw new Error("Claude API: " + msg);
    }
    const data = await res.json();

    // Fable 5 / Opus 5: 安全分類器による拒否。fallbacks:"default" 有効時は
    // 通常サーバ側で代替モデルが応答するため、ここに来るのは代替も
    // 実行できなかった場合のみ。
    if (data.stop_reason === "refusal") {
      const d = data.stop_details || {};
      const why = d.explanation || d.category || "safety refusal";
      const hint = d.recommended_model
        ? ` (推奨代替モデル: ${d.recommended_model})` : "";
      throw new Error(`Claude が要求を拒否しました: ${why}${hint}`);
    }

    const text = (data.content || []).filter(c => c.type === "text").map(c => c.text).join("\n");
    // フォールバックで別モデルが応答した場合は data.model が実際の応答モデル
    const served = data.model || m;
    const fellBack = served !== m;
    return { text, usage: data.usage || null, model: served, requested: m, fellBack };
  }

  return { complete, ENDPOINT, MODELS, DEFAULT_MODEL };
})();

if (typeof module !== "undefined" && module.exports) module.exports = ClaudeAPI;
