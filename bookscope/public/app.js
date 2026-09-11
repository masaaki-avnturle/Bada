/*
 * bookscope フロントエンド
 *  - カメラで書籍バーコード(ISBN / EAN-13)をスキャン
 *    ネイティブの BarcodeDetector API を優先し、非対応ブラウザ(iOS Safari 等)
 *    では ZXing にフォールバックする
 *  - openBD → Google Books の順で表紙と内容紹介を取得
 *  - サーバーの /api/books に登録し、一覧表示・検索・CSV 出力
 */
'use strict';

const $ = (id) => document.getElementById(id);

// ---------------- データ保存先 (サーバー API / 端末内ストレージ) ----------------
// APK 版(Android WebView)ではサーバーがないため、localStorage に保存する。
const STANDALONE =
  location.protocol === 'file:' || location.hostname === 'appassets.androidplatform.net';
const LOCAL_KEY = 'bookscope-books';

function localLoad() {
  try {
    const v = JSON.parse(localStorage.getItem(LOCAL_KEY));
    return Array.isArray(v) ? v : [];
  } catch (e) { return []; }
}
function localSave(books) { localStorage.setItem(LOCAL_KEY, JSON.stringify(books)); }
function makeId() {
  return (crypto && crypto.randomUUID)
    ? crypto.randomUUID()
    : 'id-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2);
}

const store = STANDALONE ? {
  async list() { return localLoad(); },
  async add(book) {
    const books = localLoad();
    if (book.isbn && books.some((b) => b.isbn === book.isbn)) {
      const e = new Error('duplicate'); e.status = 409; throw e;
    }
    const rec = { ...book, id: makeId(), registeredAt: new Date().toISOString() };
    books.push(rec);
    localSave(books);
    return rec;
  },
  async update(id, fields) {
    const books = localLoad();
    const book = books.find((b) => b.id === id);
    if (!book) throw new Error('not found');
    Object.assign(book, fields);
    localSave(books);
    return book;
  },
  async remove(id) { localSave(localLoad().filter((b) => b.id !== id)); },
} : {
  async list() {
    const res = await fetch('/api/books');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  },
  async add(book) {
    const res = await fetch('/api/books', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(book),
    });
    if (res.status === 409) { const e = new Error('duplicate'); e.status = 409; throw e; }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || ('HTTP ' + res.status));
    }
    return res.json();
  },
  async update(id, fields) {
    const res = await fetch(`/api/books/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fields),
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  },
  async remove(id) {
    const res = await fetch(`/api/books/${encodeURIComponent(id)}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
  },
};

// ---------------- 表紙画像の撮影・選択 ----------------
// スマホ・タブレットではカメラ撮影またはギャラリーから選択できる。
// 保存サイズを抑えるため、端末内で縮小して JPEG の data URL に変換する。

function pickCoverImage() {
  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.addEventListener('change', async () => {
      const file = input.files && input.files[0];
      if (!file) { resolve(null); return; }
      try {
        resolve(await resizeImageToDataUrl(file, 640, 0.82));
      } catch (e) {
        toast('画像の読み込みに失敗しました');
        resolve(null);
      }
    });
    input.click();
  });
}

async function resizeImageToDataUrl(file, maxSize, quality) {
  const dataUrl = await new Promise((res, rej) => {
    const reader = new FileReader();
    reader.onload = () => res(reader.result);
    reader.onerror = () => rej(new Error('read error'));
    reader.readAsDataURL(file);
  });
  const img = await new Promise((res, rej) => {
    const i = new Image();
    i.onload = () => res(i);
    i.onerror = () => rej(new Error('decode error'));
    i.src = dataUrl;
  });
  const scale = Math.min(1, maxSize / Math.max(img.width, img.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(img.width * scale));
  canvas.height = Math.max(1, Math.round(img.height * scale));
  canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/jpeg', quality);
}

// ---------------- タブ切替 ----------------

const views = { scan: $('view-scan'), list: $('view-list') };
const tabs = { scan: $('tab-scan'), list: $('tab-list') };

function showView(name) {
  for (const key of Object.keys(views)) {
    views[key].hidden = key !== name;
    tabs[key].classList.toggle('active', key === name);
  }
  if (name === 'list') refreshList();
  if (name !== 'scan') stopScanner();
}
tabs.scan.addEventListener('click', () => showView('scan'));
tabs.list.addEventListener('click', () => showView('list'));

// ---------------- ISBN ユーティリティ ----------------

function normalizeIsbn(text) {
  return String(text || '').replace(/[^0-9Xx]/g, '').toUpperCase();
}

function isValidEan13(code) {
  if (!/^\d{13}$/.test(code)) return false;
  let sum = 0;
  for (let i = 0; i < 12; i++) sum += Number(code[i]) * (i % 2 === 0 ? 1 : 3);
  return (10 - (sum % 10)) % 10 === Number(code[12]);
}

function isbn10to13(isbn10) {
  const core = '978' + isbn10.slice(0, 9);
  let sum = 0;
  for (let i = 0; i < 12; i++) sum += Number(core[i]) * (i % 2 === 0 ? 1 : 3);
  return core + String((10 - (sum % 10)) % 10);
}

// スキャン結果や手入力から「書籍の ISBN-13」を取り出す。
// 日本の書籍は 2 段バーコードで、下段(192/191 で始まる書籍JAN)は無視する。
function toBookIsbn13(raw) {
  const code = normalizeIsbn(raw);
  if (code.length === 13 && (code.startsWith('978') || code.startsWith('979'))) {
    return isValidEan13(code) ? code : null;
  }
  if (code.length === 10) {
    const isbn13 = isbn10to13(code);
    return isValidEan13(isbn13) ? isbn13 : null;
  }
  return null;
}

// ---------------- 書誌情報の取得 (openBD → Google Books) ----------------

async function fetchOpenBd(isbn13) {
  const res = await fetch(`https://api.openbd.jp/v1/get?isbn=${isbn13}`);
  if (!res.ok) return null;
  const data = await res.json();
  const entry = data && data[0];
  if (!entry || !entry.summary) return null;

  const s = entry.summary;
  let description = '';
  try {
    const texts = entry.onix.CollateralDetail.TextContent || [];
    // TextType 03 = 内容紹介, 02 = 短い紹介
    const t = texts.find((x) => x.TextType === '03') || texts.find((x) => x.TextType === '02') || texts[0];
    if (t && t.Text) description = t.Text;
  } catch (e) { /* onix に説明がない書籍もある */ }

  return {
    isbn: isbn13,
    title: s.title || '',
    author: s.author || '',
    publisher: s.publisher || '',
    pubdate: formatPubdate(s.pubdate || ''),
    cover: s.cover || '',
    description,
  };
}

async function fetchGoogleBooks(isbn13) {
  const res = await fetch(`https://www.googleapis.com/books/v1/volumes?q=isbn:${isbn13}&country=JP`);
  if (!res.ok) return null;
  const data = await res.json();
  const info = data.items && data.items[0] && data.items[0].volumeInfo;
  if (!info) return null;
  let cover = (info.imageLinks && (info.imageLinks.thumbnail || info.imageLinks.smallThumbnail)) || '';
  cover = cover.replace(/^http:/, 'https:');
  return {
    isbn: isbn13,
    title: info.title || '',
    author: (info.authors || []).join('、'),
    publisher: info.publisher || '',
    pubdate: formatPubdate(info.publishedDate || ''),
    cover,
    description: info.description || '',
  };
}

function formatPubdate(raw) {
  const d = String(raw).replace(/-/g, '');
  if (/^\d{8}$/.test(d)) return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
  if (/^\d{6}$/.test(d)) return `${d.slice(0, 4)}-${d.slice(4, 6)}`;
  return String(raw);
}

async function lookupBook(isbn13) {
  let book = null;
  try { book = await fetchOpenBd(isbn13); } catch (e) { console.warn('openBD error', e); }
  // openBD で見つからない/情報が欠けている場合は Google Books で補完
  if (!book || !book.description || !book.cover) {
    let g = null;
    try { g = await fetchGoogleBooks(isbn13); } catch (e) { console.warn('Google Books error', e); }
    if (g) {
      if (!book) book = g;
      else {
        if (!book.description) book.description = g.description;
        if (!book.cover) book.cover = g.cover;
        if (!book.pubdate) book.pubdate = g.pubdate;
      }
    }
  }
  return book;
}

// ---------------- スキャナー ----------------

const video = $('video');
const btnStart = $('btn-start');
const btnStop = $('btn-stop');
const cameraWarning = $('camera-warning');

let mediaStream = null;
let detectTimer = null;
let zxingReader = null;
let scanning = false;
let lastDetected = { code: '', at: 0 };

const secureOk = window.isSecureContext;
if (!secureOk || !navigator.mediaDevices) {
  cameraWarning.hidden = false;
  btnStart.disabled = true;
}

btnStart.addEventListener('click', startScanner);
btnStop.addEventListener('click', stopScanner);

async function startScanner() {
  if (scanning) return;
  hideResult();
  setStatus('カメラを起動しています…');
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: 'environment' }, // スマホ・タブレットの背面カメラ
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });
  } catch (e) {
    setStatus('カメラを起動できませんでした: ' + e.message, true);
    return;
  }
  video.srcObject = mediaStream;
  await video.play();
  scanning = true;
  btnStart.hidden = true;
  btnStop.hidden = false;
  setStatus('バーコードを枠内に写してください(978 で始まる上段のバーコード)');

  // Android WebView(APK 版)では BarcodeDetector が存在しても動かないことが
  // あるため、標準ブラウザでのみネイティブ API を優先し、それ以外は ZXing を使う。
  const canNative = 'BarcodeDetector' in window;
  const canZxing = !!window.ZXingBrowser;
  if (canNative && (!STANDALONE || !canZxing)) {
    const detector = new window.BarcodeDetector({ formats: ['ean_13'] });
    const tick = async () => {
      if (!scanning) return;
      try {
        const codes = await detector.detect(video);
        for (const c of codes) onCodeDetected(c.rawValue);
      } catch (e) { /* 一時的な検出エラーは無視 */ }
      detectTimer = setTimeout(tick, 250);
    };
    tick();
  } else if (canZxing) {
    // iOS Safari・Android WebView など
    zxingReader = new window.ZXingBrowser.BrowserMultiFormatReader();
    zxingReader.decodeFromVideoElement(video, (result) => {
      if (result) onCodeDetected(result.getText());
    }).catch((e) => setStatus('スキャナーの初期化に失敗しました: ' + e.message, true));
  } else {
    setStatus('このブラウザはバーコード読み取りに対応していません。手入力をご利用ください。', true);
  }
}

function stopScanner() {
  scanning = false;
  if (detectTimer) { clearTimeout(detectTimer); detectTimer = null; }
  if (zxingReader) { try { zxingReader.stopContinuousDecode(); } catch (e) {} zxingReader = null; }
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
  video.srcObject = null;
  btnStart.hidden = false;
  btnStop.hidden = true;
}

function onCodeDetected(rawValue) {
  const now = Date.now();
  // 同じコードを連続処理しない(2 秒のクールダウン)
  if (rawValue === lastDetected.code && now - lastDetected.at < 2000) return;
  lastDetected = { code: rawValue, at: now };

  const isbn13 = toBookIsbn13(rawValue);
  if (!isbn13) {
    // 書籍JAN 下段(192/191)などは案内だけ出す
    if (/^19[12]/.test(normalizeIsbn(rawValue))) {
      setStatus('下段のバーコードです。978 で始まる上段のバーコードを写してください。');
    }
    return;
  }
  if (navigator.vibrate) navigator.vibrate(80);
  stopScanner();
  handleIsbn(isbn13);
}

// ---------------- 手入力 ----------------

$('manual-form').addEventListener('submit', (ev) => {
  ev.preventDefault();
  const isbn13 = toBookIsbn13($('manual-isbn').value);
  if (!isbn13) {
    setStatus('ISBN の形式が正しくありません(978/979 で始まる 13 桁、または 10 桁)', true);
    return;
  }
  handleIsbn(isbn13);
});

// ---------------- 検索 → 登録 ----------------

let currentBook = null;

async function handleIsbn(isbn13) {
  hideResult();
  setStatus(`ISBN ${isbn13} の書籍情報を検索中…`);
  const book = await lookupBook(isbn13);
  if (!book || !book.title) {
    setStatus(`ISBN ${isbn13} の書籍情報が見つかりませんでした。`, true);
    return;
  }
  currentBook = book;
  showResult(book);
  clearStatus();
}

function showResult(book) {
  $('result-title').textContent = book.title;
  $('result-author').textContent = book.author ? `著者: ${book.author}` : '';
  $('result-publisher').textContent =
    [book.publisher, book.pubdate].filter(Boolean).join(' / ');
  $('result-isbn').textContent = `ISBN: ${book.isbn}`;

  const img = $('result-cover');
  const noCover = $('result-no-cover');
  if (book.cover) {
    img.src = book.cover;
    img.hidden = false;
    noCover.style.display = 'none';
  } else {
    img.hidden = true;
    noCover.style.display = 'flex';
  }

  const descWrap = $('result-desc-wrap');
  if (book.description) {
    $('result-desc').textContent = book.description;
    descWrap.style.display = '';
    descWrap.open = true;
  } else {
    descWrap.style.display = 'none';
  }
  $('result-card').hidden = false;
}

function hideResult() {
  $('result-card').hidden = true;
  currentBook = null;
}

$('btn-discard').addEventListener('click', hideResult);

// 検索結果カード: 表紙をカメラ撮影・ギャラリー選択した画像に差し替える
$('btn-cover-photo').addEventListener('click', async () => {
  if (!currentBook) return;
  const dataUrl = await pickCoverImage();
  if (!dataUrl) return;
  currentBook.cover = dataUrl;
  showResult(currentBook);
  toast('表紙画像を設定しました(登録ボタンで保存されます)');
});

$('btn-register').addEventListener('click', async () => {
  if (!currentBook) return;
  const btn = $('btn-register');
  btn.disabled = true;
  try {
    await store.add(currentBook);
    toast(`「${currentBook.title}」を登録しました 📚`);
    hideResult();
  } catch (e) {
    if (e.status === 409) toast('この書籍はすでに登録されています');
    else toast('登録に失敗しました: ' + e.message);
  } finally {
    btn.disabled = false;
  }
});

// ---------------- 蔵書一覧 ----------------

let allBooks = [];

async function refreshList() {
  try {
    allBooks = await store.list();
  } catch (e) {
    allBooks = [];
  }
  renderList();
}

$('search').addEventListener('input', renderList);
$('sort').addEventListener('change', renderList);
$('btn-csv').addEventListener('click', exportCsv);

function filteredBooks() {
  const q = $('search').value.trim().toLowerCase();
  let books = allBooks;
  if (q) {
    books = books.filter((b) =>
      [b.title, b.author, b.publisher, b.isbn].some((v) => String(v || '').toLowerCase().includes(q)));
  }
  const [key, dir] = $('sort').value.split('-');
  books = [...books].sort((a, b) => {
    const va = String(a[key] || '');
    const vb = String(b[key] || '');
    return dir === 'asc' ? va.localeCompare(vb, 'ja') : vb.localeCompare(va, 'ja');
  });
  return books;
}

function renderList() {
  const books = filteredBooks();
  $('list-count').textContent = `${books.length} 冊 / 全 ${allBooks.length} 冊`;
  $('list-empty').hidden = allBooks.length > 0;

  // テーブル(タブレット・PC 向け)
  const tbody = $('book-tbody');
  tbody.textContent = '';
  for (const b of books) {
    const tr = document.createElement('tr');
    tr.append(
      tdCover(b),
      td(b.title, 'title-cell'),
      td(b.author),
      td(b.publisher),
      td(b.pubdate),
      td(b.isbn, 'mono'),
      tdDesc(b),
      td((b.registeredAt || '').slice(0, 10)),
      tdActions(b),
    );
    tbody.append(tr);
  }

  // カード(スマホ向け)
  const cards = $('book-cards');
  cards.textContent = '';
  for (const b of books) cards.append(bookCard(b));
}

function td(text, cls) {
  const el = document.createElement('td');
  el.textContent = text || '';
  if (cls) el.className = cls;
  return el;
}

function tdCover(b) {
  const el = document.createElement('td');
  if (b.cover) {
    const img = document.createElement('img');
    img.className = 'cover';
    img.loading = 'lazy';
    img.src = b.cover;
    img.alt = '';
    el.append(img);
  }
  return el;
}

function tdDesc(b) {
  const el = document.createElement('td');
  el.className = 'desc-cell';
  const p = document.createElement('p');
  p.textContent = b.description || '';
  p.title = b.description || '';
  el.append(p);
  return el;
}

function tdActions(b) {
  const el = document.createElement('td');
  el.className = 'actions-cell';
  const cover = document.createElement('button');
  cover.className = 'btn';
  cover.textContent = '📷 表紙';
  cover.title = '表紙画像を撮影・選択して差し替える';
  cover.addEventListener('click', () => changeCover(b));
  const del = document.createElement('button');
  del.className = 'btn danger';
  del.textContent = '削除';
  del.addEventListener('click', () => deleteBook(b));
  el.append(cover, del);
  return el;
}

function bookCard(b) {
  const card = document.createElement('div');
  card.className = 'book-card';

  const inner = document.createElement('div');
  inner.className = 'book-card-inner';
  if (b.cover) {
    const img = document.createElement('img');
    img.className = 'cover';
    img.loading = 'lazy';
    img.src = b.cover;
    img.alt = '表紙';
    inner.append(img);
  } else {
    const nc = document.createElement('div');
    nc.className = 'no-cover';
    nc.innerHTML = '表紙<br>なし';
    inner.append(nc);
  }
  const info = document.createElement('div');
  info.className = 'book-info';
  const h2 = document.createElement('h2');
  h2.textContent = b.title;
  info.append(h2);
  for (const line of [
    b.author && `著者: ${b.author}`,
    [b.publisher, b.pubdate].filter(Boolean).join(' / '),
    b.isbn && `ISBN: ${b.isbn}`,
  ]) {
    if (!line) continue;
    const p = document.createElement('p');
    p.className = 'meta';
    p.textContent = line;
    info.append(p);
  }
  inner.append(info);
  card.append(inner);

  if (b.description) {
    const det = document.createElement('details');
    det.className = 'desc-details';
    const sum = document.createElement('summary');
    sum.textContent = '内容の概要';
    const p = document.createElement('p');
    p.textContent = b.description;
    det.append(sum, p);
    card.append(det);
  }

  const actions = document.createElement('div');
  actions.className = 'card-actions';
  const cover = document.createElement('button');
  cover.className = 'btn';
  cover.textContent = '📷 表紙を変更';
  cover.addEventListener('click', () => changeCover(b));
  const del = document.createElement('button');
  del.className = 'btn danger';
  del.textContent = '削除';
  del.addEventListener('click', () => deleteBook(b));
  actions.append(cover, del);
  card.append(actions);
  return card;
}

// 登録済みの書籍の表紙画像を撮影・選択した画像に差し替える
async function changeCover(b) {
  const dataUrl = await pickCoverImage();
  if (!dataUrl) return;
  try {
    await store.update(b.id, { cover: dataUrl });
    toast('表紙画像を更新しました');
    refreshList();
  } catch (e) {
    toast('表紙の更新に失敗しました: ' + e.message);
  }
}

async function deleteBook(b) {
  if (!confirm(`「${b.title}」を削除しますか?`)) return;
  try {
    await store.remove(b.id);
    toast('削除しました');
    refreshList();
  } catch (e) {
    toast('削除に失敗しました: ' + e.message);
  }
}

function exportCsv() {
  const header = ['ISBN', 'タイトル', '著者', '出版社', '出版日', '概要', '表紙URL', '登録日'];
  const esc = (v) => '"' + String(v || '').replace(/"/g, '""') + '"';
  // 撮影した表紙 (data URL) は巨大なので CSV には URL のみ出力する
  const coverText = (c) => (String(c || '').startsWith('data:') ? '(撮影画像)' : c);
  const rows = filteredBooks().map((b) =>
    [b.isbn, b.title, b.author, b.publisher, b.pubdate, b.description, coverText(b.cover), b.registeredAt].map(esc).join(','));
  const bom = '\uFEFF'; // Excel で文字化けしないよう BOM を付ける
  const blob = new Blob([bom + header.map(esc).join(',') + '\n' + rows.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'bookscope.csv';
  a.click();
  URL.revokeObjectURL(a.href);
}

// ---------------- 共通 UI ----------------

function setStatus(msg, isError) {
  const el = $('lookup-status');
  el.textContent = msg;
  el.classList.toggle('error', !!isError);
  el.hidden = false;
}
function clearStatus() { $('lookup-status').hidden = true; }

let toastTimer = null;
function toast(msg) {
  const el = $('toast');
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 3000);
}

// 初期表示
showView('scan');
