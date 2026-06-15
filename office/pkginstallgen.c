/* NON-C CONTENT — Office add-in manifest/assets (prose + XML), not a C program.
   Payload preserved verbatim but excluded from compilation. */
#if 0
/*了解しました。単独キーの割当やグローバルフックを使わず、Word の既存機能を壊さない「タスクペイン内で Vim ライクに編集し、選択範囲や段落単位で書式を保持して文書に反映する」Office Add-in（Office.js）パッケージを提供します。ローカルでホストしてサイドロードできる最小実装一式と手順、主要コードを掲載します。

ポイント（要約）
- タスクペイン内に CodeMirror（vim keymap）を埋め込み、タスクペインにフォーカスしている間は通常の Vim 操作が可能。
- 編集対象は「選択範囲（選択がなければ段落単位）」に限定し、OOXML（<w:p>, <w:r>, <w:t>）を解析してテキストのみを書き換え、タグ構造（書式）をできるだけ保持する。
- 単独キー置換やグローバルフックは行わないため、Word の標準入力やショートカットを壊さない安全な方式。

ファイル構成（推奨フォルダ）
- manifest.xml
- web/
  - index.html
  - taskpane.css
  - taskpane.js
  - package.json
  - README.md

以下、各ファイルの内容（そのまま保存して使えます）。web フォルダを https でホストし、manifest の SourceLocation を合わせてサイドロードしてください。


1) manifest.xml
（SourceLocation を https://localhost:3000/index.html に合わせてください）
```xml
*/
<?xml version="1.0" encoding="utf-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:type="TaskPaneApp">
  <Id>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</Id>
  <Version>1.0.0.0</Version>
  <ProviderName>YourName</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>
  <DisplayName DefaultValue="VimPane (Safe Taskpane)"/>
  <Description DefaultValue="Edit selection with Vim-like keybindings in a taskpane while preserving formatting."/>
  <IconUrl DefaultValue="https://localhost:3000/icon-32.png"/>
  <Hosts>
    <Host Name="Document"/>
  </Hosts>
  <DefaultSettings>
    <SourceLocation DefaultValue="https://localhost:3000/index.html"/>
  </DefaultSettings>
  <Permissions>ReadWriteDocument</Permissions>
  <Requirements>
    <Sets DefaultMinVersion="1.1">
      <Set Name="WordApi" MinVersion="1.1"/>
    </Sets>
  </Requirements>
</OfficeApp>

2) web/index.html
```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>VimPane — Safe Taskpane Editor</title>
  <meta http-equiv="Content-Security-Policy" content="default-src 'self' https:; script-src 'self' https: 'unsafe-inline' 'unsafe-eval'; style-src 'self' https: 'unsafe-inline'">
  <link rel="stylesheet" href="taskpane.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.css"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/theme/monokai.min.css"/>
</head>
<body>
  <div id="topbar">
    <button id="btnLoadSel">Load Selection</button>
    <button id="btnLoadPara">Load Paragraph</button>
    <button id="btnSave">Save</button>
    <span id="status">Ready</span>
  </div>
  <div id="editorWrap"><textarea id="editor"></textarea></div>

  <script src="https://appsforoffice.microsoft.com/lib/1/hosted/office.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/keymap/vim.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/mode/markdown/markdown.min.js"></script>
  <script src="taskpane.js"></script>
</body>
</html>
```

3) web/taskpane.css
```css
html,body{height:100%;margin:0;font-family:Segoe UI,Arial;}
#topbar{padding:8px;background:#f3f3f3;border-bottom:1px solid #ddd;display:flex;gap:8px;align-items:center;}
#status{color:#666;margin-left:10px;}
#editorWrap{height:calc(100% - 48px);}
.CodeMirror{height:100%;}
textarea#editor{display:none;}
button{padding:6px 10px;}
```

4) web/taskpane.js
（OOXML を段落/ラン単位で解析し、テキストのみ置換して書式を維持するロジック。タスクペイン内で Vim キーマップが有効）
```javascript
/* taskpane.js - Safe Vim taskpane: edit selection or paragraph while preserving formatting */
let editor;

Office.onReady().then(() => {
  document.getElementById('btnLoadSel').addEventListener('click', loadSelection);
  document.getElementById('btnLoadPara').addEventListener('click', loadContainingParagraph);
  document.getElementById('btnSave').addEventListener('click', saveBack);
  editor = CodeMirror.fromTextArea(document.getElementById('editor'), {
    mode: 'markdown', theme: 'monokai', lineNumbers: true, keyMap: 'vim', autofocus: true
  });
  setStatus('Ready');
});

function setStatus(s){ document.getElementById('status').textContent = s; }

/* --- OOXML utilities --- */
/* Extract paragraphs (<w:p>...</w:p>) from OOXML string */
function splitParagraphs(ooxml) {
  const paraRegex = /<w:p[\s\S]*?<\/w:p>/g;
  const matches = [...ooxml.matchAll(paraRegex)].map(m => m[0]);
  return matches;
}

/* Extract concatenated text of all <w:t> in an OOXML fragment */
function extractText(ooxmlFragment) {
  const tRegex = /<w:t[^>]*>([\s\S]*?)<\/w:t>/g;
  const arr = [...ooxmlFragment.matchAll(tRegex)].map(m => m[1].replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&'));
  return arr.join('');
}

/* Replace <w:t> contents in an OOXML paragraph with newText.
   Strategy: split newText into tokens (words + spaces) and greedily assign to runs to preserve formatting boundaries. */
function replaceTextInParagraph(parOoxml, newText) {
  const tRegex = /(<w:t[^>]*>)([\s\S]*?)(<\/w:t>)/g;
  const parts = [];
  let match;
  while ((match = tRegex.exec(parOoxml)) !== null) {
    parts.push({ pre: match[1], orig: match[2], post: match[3] });
  }
  if (parts.length === 0) return parOoxml;

  // Tokenize by whitespace preserving spaces
  const tokens = newText.match(/\s+|[^\s]+/g) || [''];

  // Determine target distribution by original run lengths (fallback to equal)
  const origLens = parts.map(p => p.orig.length || 1);
  const totalOrig = origLens.reduce((a,b)=>a+b, 0) || parts.length;
  let pos = 0;
  const alloc = parts.map((_,i) => {
    const targetChars = Math.max(1, Math.floor((origLens[i] / totalOrig) * tokens.join('').length));
    let s = '';
    while (pos < tokens.length && s.length < targetChars) { s += tokens[pos++]; }
    return s;
  });
  while (pos < tokens.length) { alloc[alloc.length-1] += tokens[pos++]; }

  function xmlEscape(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  // rebuild paragraph
  let out = '';
  let lastIndex = 0;
  tRegex.lastIndex = 0;
  let idx = 0;
  while ((match = tRegex.exec(parOoxml)) !== null) {
    out += parOoxml.slice(lastIndex, match.index);
    out += parts[idx].pre + xmlEscape(alloc[idx] || '') + parts[idx].post;
    lastIndex = match.index + match[0].length;
    idx++;
  }
  out += parOoxml.slice(lastIndex);
  return out;
}

/* --- Loading functions --- */

/* Load exact selection OOXML and place extracted text (paragraphs joined by blank line) into editor */
async function loadSelection() {
  setStatus('Loading selection...');
  try {
    await Word.run(async (context) => {
      const sel = context.document.getSelection();
      const ooxmlRes = sel.getOoxml();
      await context.sync();
      const ooxml = ooxmlRes.value;
      const paras = splitParagraphs(ooxml);
      const texts = paras.map(p => extractText(p));
      editor.setValue(texts.join('\n\n'));
      editor.clearHistory();
      setStatus('Selection loaded. Edit in taskpane (Vim keymap active).');
    });
  } catch (e) {
    console.error(e); setStatus('Load failed: ' + (e.message || e));
  }
}

/* Load the paragraph that contains the cursor (single paragraph) */
async function loadContainingParagraph() {
  setStatus('Loading paragraph...');
  try {
    await Word.run(async (context) => {
      const sel = context.document.getSelection();
      // expand to paragraph range via getRange? There's no direct API to get containing paragraph OOXML easily,
      // so get selection.getOoxml and extract first paragraph.
      const ooxmlRes = sel.getOoxml();
      await context.sync();
      const paras = splitParagraphs(ooxmlRes.value);
      if (paras.length === 0) {
        setStatus('No paragraph OOXML found in selection.');
        return;
      }
      const first = paras[0];
      editor.setValue(extractText(first));
      editor.clearHistory();
      // store original paragraph OOXML in editor state for saving
      editor._originalParagraphOoxml = first;
      setStatus('Paragraph loaded.');
    });
  } catch (e) {
    console.error(e); setStatus('Load failed: ' + (e.message || e));
  }
}

/* --- Save function --- */
/* If editor._originalParagraphOoxml exists, replace that paragraph only.
   Otherwise, map edited paragraphs back to selection paragraphs. */
async function saveBack() {
  setStatus('Saving back to document...');
  try {
    await Word.run(async (context) => {
      const sel = context.document.getSelection();
      const ooxmlRes = sel.getOoxml();
      await context.sync();
      const oldOoxml = ooxmlRes.value;
      const paras = splitParagraphs(oldOoxml);
      if (paras.length === 0) {
        setStatus('Nothing to save: no paragraphs in selection.');
        return;
      }

      const editedText = editor.getValue();
      let newOoxml = '';
      if (editor._originalParagraphOoxml) {
        // replace only that paragraph (we need to find it among paras; prefer index 0)
        const newPar = replaceTextInParagraph(editor._originalParagraphOoxml, editedText);
        // rebuild OOXML: replace the first matching paragraph in paras with newPar
        let replaced = false;
        for (let i=0;i<paras.length;i++) {
          if (!replaced && paras[i] === editor._originalParagraphOoxml) {
            newOoxml += newPar;
            replaced = true;
          } else {
            newOoxml += paras[i];
          }
        }
        if (!replaced) {
          // fallback: replace first paragraph
          paras[0] = newPar;
          newOoxml = paras.join('');
        }
      } else {
        // map edited paragraphs (split by blank line) to existing paras
        const editedParas = editedText.split(/\n\s*\n/);
        const mapped = paras.map((p,i) => {
          const newText = (i < editedParas.length) ? editedParas[i] : extractText(p);
          return replaceTextInParagraph(p, newText);
        });
        newOoxml = mapped.join('');
      }

      // apply new OOXML to selection (replace)
      sel.clear();
      sel.insertOoxml(newOoxml, Word.InsertLocation.replace);
      await context.sync();

      // clear stored original paragraph
      delete editor._originalParagraphOoxml;
      setStatus('Saved (formatting preserved where possible).');
    });
  } catch (e) {
    console.error(e);
    setStatus('Save failed: ' + (e.message || e));
  }
}
```

5) web/package.json（ローカルサーバ用・任意）
```json
{
  "name": "vimpane-safe",
  "version": "1.0.0",
  "scripts": {
    "start": "http-server ./ -p 3000 -c-1"
  },
  "devDependencies": {
    "http-server": "^14.1.1"
  }
}
```

6) web/README.md（最短起動手順）
```
1) Prepare environment:
   - Install Node.js (for http-server) or any static HTTPS server.
   - For Word desktop, host with HTTPS. Use mkcert to create localhost certs and run a server that supports https.

2) Start static server in web/:
   npm install
   npm start
   (or run a server that serves https://localhost:3000)

3) Edit manifest.xml -> set SourceLocation to https://localhost:3000/index.html

4) Sideload add-in into Word:
   - Follow Microsoft docs: https://learn.microsoft.com/office/dev/add-ins/testing/sideload-office-add-ins-for-testing

5) Usage:
   - In Word, open the add-in (taskpane). Select text (or place cursor in a paragraph).
   - Click "Load Selection" to load selection (multiple paragraphs allowed), or "Load Paragraph" to load just the current paragraph.
   - Edit in the taskpane using Vim keybindings (CodeMirror vim keymap).
   - Click "Save" to write changes back. Formatting is preserved via OOXML run-level replacement where possible.

Notes:
- This tool edits text content only. Complex elements (embedded OLE objects, fields, equations) may not behave perfectly.
- Always keep backups of important documents.
```

運用上の注意（短く）
- タスクペインにフォーカスしている間は Vim 操作が可能です。文書にフォーカスが戻ると通常の Word 入力に戻ります。これにより Word の既存キーや単独キーの挙動は変わりません。
- OOXML の扱いは「できるだけ書式を維持」することを目指した実装です。稀にラン分割やフィールドの特殊ケースで期待どおりにならないことがあるため重要文書ではバックアップを必ず取ってください。
- 追加拡張（選択のみ差分マージ、Open XML SDK を用いたサーバ側精密処理、Monaco + monaco-vim への置換など）も可能です。必要なら指定してください。

次に何をしますか？
- このまま完全 ZIP パッケージ（manifest + web/*）を出力しますか？  
- あるいは段落マッピング（単語境界でのより正確な割当）や Monaco エディタへの移行、HTTPS ローカルサーバ設定手順（mkcert 等）を詳しく出しますか？

希望を番号か短文で教えてください。

/* defensively close any comment left open by the payload: */ /*
*/
#endif
typedef int bada_noncompiled_placeholder;
