/*
 * opener.js — 検索ヒットを BadaCineVim で開く共通ロジック (complete.html / index.html 共用)
 *
 *   ・ソース/テキスト … CineVim (Vim エディタ) で開き、:w で保存
 *   ・PDF            … BadaPdfView (ページ表示 + 注釈編集) で開き、:w で PDF に保存。
 *                      「⌨ テキスト」で抽出テキスト (CineVim・該当行ジャンプ) と行き来でき、
 *                      同じ場所に原稿の .tex があれば「📝 .tex を編集」で開ける。
 *
 * bridge は Electron (badaSearch) / ブラウザ・APK (searchweb) / デモのいずれか。
 * fileBytes / saveBytes を持たないブリッジでは PDF もテキスト表示にフォールバックします。
 */
(function (global) {
  "use strict";

  function texPathOf(p) { return /\.pdf$/i.test(p) ? p.replace(/\.pdf$/i, ".tex") : null; }

  function open(bridge, o) {
    o = o || {};
    var say = typeof o.setStatus === "function" ? o.setStatus : function () {};
    var p = o.path, CV = global.BadaCineVim, PV = global.BadaPdfView;
    if (!bridge || !CV) { say("CineVim を読み込めません"); return Promise.resolve(null); }

    function findTex() {
      var tex = texPathOf(p);
      if (!tex) return Promise.resolve(null);
      return Promise.resolve(bridge.fileText(tex)).then(function (r) { return r && !r.error ? tex : null; },
                                                        function () { return null; });
    }
    function texAction(tex) {
      return { label: "📝 .tex を編集", title: "この PDF の原稿 (LaTeX ソース) を CineVim で編集",
               onClick: function (c) { c.close(); open(bridge, { path: tex, line: 1, query: o.query, setStatus: say }); } };
    }

    function openText(res, tex) {
      var isPdf = res.lang === "PDF", actions = [];
      if (isPdf && PV && bridge.fileBytes) {
        actions.push({ label: "📄 PDF 表示", title: "ページ表示に切り替えて注釈編集",
                       onClick: function (c) { c.close(); openPdf(res, tex); } });
      }
      if (tex) actions.push(texAction(tex));
      return CV.open({
        name: res.name, lines: res.lines, lang: res.lang, readonly: res.readonly,
        readonlyHint: isPdf ? "PDF の抽出テキストです — 編集は「📄 PDF 表示」(注釈)" + (tex ? " か「📝 .tex を編集」" : "") + " で" : "",
        gotoLine: o.line, search: o.query, actions: actions,
        onSave: function (text) { return Promise.resolve(bridge.saveFile(p, text)); }
      });
    }

    function openPdf(res, tex) {
      return Promise.resolve(bridge.fileBytes(p)).then(function (r) {
        if (!r || r.error || !r.bytes) {
          say("⚠ PDF をページ表示できません (" + ((r && r.error) || "読み込み不可") + ") — テキスト表示で開きます");
          return openText(res, tex);
        }
        return PV.open({
          name: res.name, bytes: r.bytes, search: o.query,
          readonly: typeof bridge.saveBytes !== "function",
          actions: tex ? [texAction(tex)] : [],
          onSave: function (out) { return Promise.resolve(bridge.saveBytes(p, out)); },
          onTextMode: function () {
            /* 保存した注釈 (メモ) が抽出テキストに反映されるよう読み直す */
            Promise.resolve(bridge.fileText(p)).then(function (again) { openText(again && !again.error ? again : res, tex); });
          }
        });
      });
    }

    return Promise.resolve(bridge.fileText(p)).then(function (res) {
      if (!res || res.error) { say("⚠ " + ((res && res.error) || "ファイルを開けません")); return null; }
      if (res.lang !== "PDF") return openText(res, null);
      return findTex().then(function (tex) {
        if (o.mode === "text" || !PV || !bridge.fileBytes) return openText(res, tex);
        return openPdf(res, tex);
      });
    });
  }

  global.BadaOpen = { open: open, texPathOf: texPathOf };
})(typeof globalThis !== "undefined" ? globalThis : this);
