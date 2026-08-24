/* ============================================================================
 *  respond.js — BadaGPT 質問応答エンジン (ローカル / オフライン)
 *
 *  アップロードされたファイル(PDF 等はテキストへ自動変換済み)を実際に読み、
 *  質問・要望に応じた解答を構成する:
 *
 *    1) 文分割     — 日本語 (。!?) / 英語 (.) / 改行 で文に分割
 *    2) キーワード — 質問から内容語 (漢字・カタカナ・英数語) を抽出
 *    3) 検索       — ζ-Zipf 重み付き TF スコアで関連文を上位抽出
 *    4) 構成       — 要望種別 (要約/論文/アプリ/コード/数式/英語/予知/レビュー)
 *                    ごとに、抽出文から解答・論文・実行可能 HTML アプリ・
 *                    Python コードを組み立てる
 *
 *  すべて標準 JavaScript のみ。Claude API キーがあれば、この解答を種として
 *  Claude が精緻化する (claude.js / index.html 参照)。
 * ==========================================================================*/
"use strict";

const Responder = (() => {

  // ---- 1) 文分割 ----------------------------------------------------------
  function segment(text) {
    if (!text) return [];
    const rough = text
      .replace(/\r/g, "")
      .split(/(?<=[。!?!?])|(?<=\.)\s+(?=[A-Z0-9])|\n{2,}/);
    const out = [];
    for (let s of rough) {
      s = s.replace(/\s+/g, " ").trim();
      if (s.length >= 8 && s.length <= 400) out.push(s);
    }
    return out;
  }

  // ---- 2) 質問からキーワード抽出 ------------------------------------------
  const STOP = new Set([
    "して", "ください", "下さい", "する", "です", "ます", "こと", "もの",
    "ような", "ように", "から", "まで", "など", "について", "における",
    "投稿", "資料", "ファイル", "作成", "生成", "提示", "説明",
    "the", "and", "for", "with", "from", "this", "that", "please"
  ]);
  function keywords(prompt) {
    const raw = (prompt || "").match(/[一-龯々]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}/g) || [];
    const ks = [];
    for (const w of raw) {
      const lw = w.toLowerCase();
      if (STOP.has(w) || STOP.has(lw)) continue;
      if (!ks.includes(w)) ks.push(w);
    }
    return ks.slice(0, 12);
  }

  // ---- 3) ζ-Zipf 重み付き検索 ---------------------------------------------
  // キーワード k 番目の重みを Zipf/ゼータ的に 1/(rank)^0.5 で減衰させ、
  // 文中の出現回数 × 語長で加点。文長で正規化。
  function scoreSentence(sent, keys) {
    let sc = 0;
    for (let r = 0; r < keys.length; r++) {
      const k = keys[r];
      let idx = 0, hits = 0;
      const target = sent.toLowerCase(), kk = k.toLowerCase();
      while ((idx = target.indexOf(kk, idx)) >= 0) { hits++; idx += kk.length; }
      if (hits) sc += hits * k.length * Math.pow(r + 1, -0.5);
    }
    return sc / Math.sqrt(sent.length);
  }

  function retrieve(files, prompt, topK) {
    const keys = keywords(prompt);
    const cands = [];
    for (const f of files || []) {
      const sents = segment(f.text || "");
      for (const s of sents) cands.push({ s, src: f.name, sc: scoreSentence(s, keys) });
    }
    cands.sort((a, b) => b.sc - a.sc);
    let hits = cands.filter(c => c.sc > 0).slice(0, topK);
    // キーワード一致ゼロなら文書の先頭側から代表文を取る (常に資料に根ざす)
    if (!hits.length) hits = cands.slice(0, Math.min(topK, cands.length));
    return { hits, keys, total: cands.length };
  }

  // ---- 数式らしい行の抽出 --------------------------------------------------
  function extractEquations(files, cap = 12) {
    const out = [];
    for (const f of files || []) {
      for (const line of (f.text || "").split(/\n/)) {
        const t = line.trim();
        if (t.length < 4 || t.length > 160) continue;
        if (/[=∫Σ∬ζΓβπ√∞≒≈≦≧±×÷]|\\frac|\^[0-9(]|_\{/.test(t) && /[=∫Σ∬≒≈]/.test(t)) {
          out.push({ eq: t, src: f.name });
          if (out.length >= cap) return out;
        }
      }
    }
    return out;
  }

  // ---- 4) 要望種別の判定 ----------------------------------------------------
  function detectIntent(prompt) {
    const p = prompt || "";
    if (/論文|paper/i.test(p)) return "paper";
    if (/アプリ|application|\bapp\b|HTML/i.test(p)) return "app";
    if (/コード|実装|code|implement|python/i.test(p)) return "code";
    if (/数式|equation|数理/i.test(p)) return "equations";
    if (/英語|english/i.test(p)) return "english";
    if (/予知|続き|predict|continuation/i.test(p)) return "prediction";
    if (/レビュー|批判|review/i.test(p)) return "review";
    if (/要約|summar|まとめ/i.test(p)) return "summary";
    return "answer";
  }

  const bullets = hits => hits.map(h => `- ${h.s} — *(${h.src})*`).join("\n");
  const esc = s => (s || "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // ---- 実行可能 HTML アプリの生成 (資料ビューア + 検索) ---------------------
  function buildAppHtml(title, hits, keys) {
    const data = hits.map(h => ({ t: h.s, src: h.src }));
    return `<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<style>
 body{background:#04060a;color:#e8eef8;font-family:system-ui,"Noto Sans JP",sans-serif;
      max-width:720px;margin:0 auto;padding:16px;line-height:1.7}
 h1{color:#c8a44a;font-size:18px}
 input{width:100%;background:#05080e;border:1px solid #1b2740;border-radius:9px;
       color:#e8eef8;padding:10px;font-size:14px;box-sizing:border-box}
 .item{background:#0a0f18;border:1px solid #1b2740;border-radius:10px;padding:12px;margin-top:10px;font-size:14px}
 .src{color:#8ea0bc;font-size:11px;margin-top:6px}
 mark{background:#c8a44a;color:#04060a;border-radius:3px;padding:0 2px}
 .stat{color:#40b8c0;font-size:12px;margin:8px 0}
</style></head><body>
<h1>β ${esc(title)}</h1>
<input id="q" placeholder="検索語を入力 (資料から抽出した ${data.length} 文を検索)">
<div class="stat" id="stat"></div>
<div id="list"></div>
<script>
const DATA = ${JSON.stringify(data)};
const q = document.getElementById("q"), list = document.getElementById("list"), stat = document.getElementById("stat");
function render(f){
  const rows = DATA.filter(d => !f || d.t.toLowerCase().includes(f.toLowerCase()));
  stat.textContent = rows.length + " / " + DATA.length + " 文";
  list.innerHTML = rows.map(d => {
    let t = d.t.replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
    if (f) t = t.replace(new RegExp(f.replace(/[.*+?^\${}()|[\\]\\\\]/g,"\\\\$&"),"gi"), m => "<mark>"+m+"</mark>");
    return '<div class="item">'+t+'<div class="src">'+d.src+'</div></div>';
  }).join("");
}
q.addEventListener("input", () => render(q.value.trim()));
render("");
<\/script>
</body></html>`;
  }

  // ---- Python コードの生成 (抽出データ + ζ 解析) ----------------------------
  function buildPython(hits, keys, tele) {
    const data = hits.slice(0, 8).map(h => JSON.stringify(h.s)).join(",\n    ");
    return `# BadaGPT generated: 資料 (PDF→テキスト変換済み) に基づく解析コード
import math

KEYWORDS = ${JSON.stringify(keys)}
EXTRACTED = [
    ${data}
]

def zeta(s, N=64):
    total = sum(n ** -s for n in range(1, N))
    return total + N ** (1 - s) / (s - 1) + 0.5 * N ** -s

def zeta_entropy(s, h=1e-4):
    z = zeta(s)
    zp = (zeta(s + h) - zeta(s - h)) / (2 * h)
    return s * (-zp / z) + math.log(z)   # H(s) [nat]

def search(word):
    """抽出文からキーワード検索 (資料に根ざした回答の根拠提示)"""
    return [t for t in EXTRACTED if word.lower() in t.lower()]

if __name__ == "__main__":
    s = ${tele ? tele.s : 1.5}
    print("zeta(s)    =", zeta(s))
    print("H(s) [nat] =", zeta_entropy(s))
    for k in KEYWORDS[:3]:
        print(f"hits[{k}] =", len(search(k)))`;
  }

  // ---- 解答の構成 -----------------------------------------------------------
  function answer(prompt, files, local) {
    const intent = detectIntent(prompt);
    const { hits, keys } = retrieve(files, prompt, intent === "app" ? 20 : 8);
    const tele = local && local.telemetry;
    const hasFiles = files && files.length;
    const srcList = hasFiles ? files.map(f => `\`${f.name}\` (${f.kind})`).join(", ") : "(資料なし)";
    const head = `# BadaGPT 解答\n\n**質問:** ${prompt}\n**読み込んだ資料:** ${srcList}\n**抽出キーワード:** ${keys.join(", ") || "(なし)"}\n\n`;
    const zetaNote = tele
      ? `\n\n## ζ-Entropy テレメトリ\n- s = ${tele.s}, ζ(s) = ${tele.zeta}, H(s) = ${tele.entropy_nat} nat / ${tele.entropy_bit} bit, τ = ${tele.temperature}\n`
      : "";

    if (!hasFiles) {
      return head +
        `## 回答\n資料が投稿されていないため、一般回答になります。PDF などの資料を` +
        `アップロードすると自動でテキスト変換され、その内容に基づいて回答します。\n` +
        (local ? `\n## ζ-Entropy 予知\n> ${local.text}\n` : "") + zetaNote;
    }

    switch (intent) {
      case "summary":
        return head + `## 要約 (資料からの抽出)\n${bullets(hits)}\n\n` +
          `## 結論\n資料の核心は「${keys.slice(0, 3).join("・") || "上記"}」に関する上記 ${hits.length} 点に集約されます。` + zetaNote;

      case "paper": {
        const intro = hits.slice(0, 2), theory = hits.slice(2, 5), rest = hits.slice(5, 7);
        const eqs = extractEquations(files);
        return head +
          `## 論文\n\n### 1. 序論\n${intro.map(h => h.s).join(" ")}\n\n` +
          `### 2. 理論\n${theory.map(h => `${h.s} *(${h.src})*`).join("\n\n") || "(資料から理論記述を抽出できませんでした)"}\n\n` +
          `### 3. 数式\n${eqs.length ? eqs.map(e => `- \`${e.eq}\` *(${e.src})*`).join("\n") : "- H(s) = s·(−ζ′(s)/ζ(s)) + log ζ(s)\n- ζ(s) = β(p,q)/log x"}\n\n` +
          `### 4. 結論\n${rest.map(h => h.s).join(" ") || "本稿では資料の核心を ζ-Entropy 統計の下で整理した。"}\n\n` +
          `*(この論文は「⬇ 解答を PDF」でそのまま PDF 保存できます)*` + zetaNote;
      }

      case "app": {
        const title = (keys.slice(0, 2).join(" ") || "資料") + " ビューア";
        return head +
          `## アプリケーション\n資料から抽出した ${hits.length} 文を検索・閲覧できる単一ファイル HTML アプリを生成しました。` +
          `「⬇ アプリ (.html)」でダウンロードすると、そのまま実行できます。\n\n` +
          "```html\n" + buildAppHtml(title, hits, keys) + "\n```\n" + zetaNote;
      }

      case "code":
        return head +
          `## 実装コード\n資料の抽出文とキーワードを埋め込んだ Python 解析コードです` +
          `(「⬇ ソースコード」で保存できます)。\n\n` +
          "```python\n" + buildPython(hits, keys, tele) + "\n```\n\n" +
          `## 根拠 (資料からの抽出)\n${bullets(hits.slice(0, 4))}` + zetaNote;

      case "equations": {
        const eqs = extractEquations(files);
        return head +
          `## 資料中の数式\n${eqs.length ? eqs.map(e => `- \`${e.eq}\` *(${e.src})*`).join("\n") : "(数式らしい行は検出されませんでした)"}\n\n` +
          `## エンジンの数理\n- ζ(s) = Σ n^−s, H(s) = s·(−ζ′(s)/ζ(s)) + log ζ(s)\n- β(p,q) = Γ(p)Γ(q)/Γ(p+q), ζ(s) = β(p,q)/log x\n\n` +
          `## 文脈 (資料からの抽出)\n${bullets(hits.slice(0, 4))}` + zetaNote;
      }

      case "english":
        return head +
          `## English Summary (extractive)\nKey passages from the uploaded material` +
          ` (keywords: ${keys.join(", ") || "n/a"}):\n\n${bullets(hits)}\n\n` +
          `*Note: for a fully translated English summary, switch to the Claude API mode.*` + zetaNote;

      case "prediction":
        return head +
          `## 文脈 (資料からの抽出)\n${bullets(hits.slice(0, 4))}\n\n` +
          `## ζ-Entropy 未知事前予知 (資料の続き)\n> ${local ? local.text : "(エンジン未実行)"}\n` + zetaNote;

      case "review":
        return head +
          `## レビュー\n\n### 強み (資料より)\n${bullets(hits.slice(0, 3))}\n\n` +
          `### 疑問点\n${hits.slice(3, 5).map(h => `- 「${h.s.slice(0, 60)}…」の根拠・定義をより明確にできるか *(${h.src})*`).join("\n") || "- (追加の抽出文なし)"}\n\n` +
          `### 改善案\n- 主要キーワード (${keys.slice(0, 3).join("・") || "core terms"}) の定義節を冒頭に置く\n` +
          `- 数式と本文の対応を明示する\n- 実験・数値例を追加する` + zetaNote;

      default: // answer
        return head +
          `## 回答\n${hits.length ? `資料に基づく関連箇所は以下の通りです:\n\n${bullets(hits)}\n\n` +
            `これらから、「${keys.slice(0, 3).join("・") || "ご質問"}」については上記 ${hits.length} 点が資料の答えに相当します。`
            : "資料から関連箇所を見つけられませんでした。質問の語を変えてお試しください。"}` + zetaNote;
    }
  }

  return { answer, detectIntent, retrieve, keywords, segment, extractEquations };
})();

if (typeof module !== "undefined" && module.exports) module.exports = Responder;
