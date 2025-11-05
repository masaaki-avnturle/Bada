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

