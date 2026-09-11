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

// アプリのバージョン (端末に入っている APK が最新かどうかの確認用に表示する)
const APP_VERSION = '1.5';
$('app-version').textContent = 'v' + APP_VERSION;

// 端末上で起きたエラーを画面に出す (原因調査をしやすくするため)
window.addEventListener('error', (ev) => {
  try { toast('エラー: ' + (ev.message || '不明なエラー')); } catch (e) { /* noop */ }
});

// http:// の表紙 URL は https ページ (APK 版含む) では混在コンテンツとして
// ブロックされ画像が写らないため、常に https:// に直して使う
function httpsCover(url) {
  const u = String(url || '');
  return u.indexOf('http://') === 0 ? 'https://' + u.slice(7) : u;
}

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
// 「カメラで撮影」はアプリ内のカメラ画面 (getUserMedia) で撮影する。
// バーコードスキャンと同じ仕組みなので APK 版 (WebView) でも確実に動く。
// 「画像から選択」は DOM に常駐させた file input を使う。
// 保存サイズを抑えるため、いずれも端末内で縮小して JPEG の data URL にする。

const COVER_MAX_SIZE = 640;

// 登録方法の選択シートを出し、選ばれた方法で表紙 (data URL または画像 URL) を
// 返す (キャンセル・取得失敗は null)。isbn を渡すと「ISBN から取得」も選べる。
function chooseCoverImage(isbn) {
  return new Promise((resolve) => {
    const sheet = $('cover-sheet');
    const btnIsbn = $('btn-sheet-isbn');
    const btnCamera = $('btn-sheet-camera');
    // ISBN がない書籍では ISBN 取得ボタンを隠す
    btnIsbn.hidden = !toBookIsbn13(isbn);
    // カメラが使えない環境 (HTTP 接続の PC など) では撮影ボタンを無効化
    btnCamera.disabled = !(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    sheet.hidden = false;
    btnIsbn.onclick = async () => {
      sheet.hidden = true;
      toast('ISBN から表紙を検索しています…');
      const url = await fetchCoverByIsbn(isbn);
      if (!url) toast('この ISBN の表紙が見つかりませんでした');
      resolve(url);
    };
    btnCamera.onclick = () => { sheet.hidden = true; captureCoverPhoto().then(resolve); };
    $('btn-sheet-file').onclick = () => { sheet.hidden = true; pickCoverFile().then(resolve); };
    $('btn-sheet-cancel').onclick = () => { sheet.hidden = true; resolve(null); };
  });
}

// アプリ内カメラで表紙を撮影する
let coverStream = null;
async function captureCoverPhoto() {
  stopScanner(); // バーコード用カメラと競合しないように止める
  const overlay = $('cover-camera');
  const video = $('cover-video');
  try {
    coverStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1280 },
        height: { ideal: 1280 },
      },
      audio: false,
    });
  } catch (e) {
    toast('カメラを起動できませんでした: ' + e.message);
    return null;
  }
  overlay.hidden = false;
  video.srcObject = coverStream;
  try { await video.play(); } catch (e) { /* 停止時の中断は無視 */ }

  return new Promise((resolve) => {
    const finish = (value) => {
      if (coverStream) {
        coverStream.getTracks().forEach((t) => t.stop());
        coverStream = null;
      }
      video.srcObject = null;
      overlay.hidden = true;
      resolve(value);
    };
    $('btn-shoot').onclick = () => {
      const w = video.videoWidth;
      const h = video.videoHeight;
      if (!w || !h) { toast('映像の準備ができていません'); return; }
      const scale = Math.min(1, COVER_MAX_SIZE / Math.max(w, h));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(w * scale));
      canvas.height = Math.max(1, Math.round(h * scale));
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      finish(canvas.toDataURL('image/jpeg', 0.85));
    };
    $('btn-shoot-cancel').onclick = () => finish(null);
  });
}

// ギャラリー・ファイルから表紙画像を選択する
function pickCoverFile() {
  return new Promise((resolve) => {
    const input = $('cover-file');
    input.value = '';
    input.onchange = async () => {
      const file = input.files && input.files[0];
      if (!file) { resolve(null); return; }
      try {
        resolve(await resizeImageToDataUrl(file, COVER_MAX_SIZE, 0.82));
      } catch (e) {
        toast('画像の読み込みに失敗しました');
        resolve(null);
      }
    };
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
    cover: httpsCover(s.cover),
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
  cover = httpsCover(cover);
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
  // 表紙は「実際に表示できる URL」を ISBN から解決して登録する
  if (book) {
    const cover = await resolveCoverUrl(isbn13, book.cover);
    book.cover = cover || book.cover || '';
  }
  return book;
}

// ---------------- ISBN からの表紙取得 ----------------
// openBD / 国立国会図書館 (NDL) 書影 / Google Books の順に候補を試し、
// 実際に読み込めた画像の URL を返す (見つからなければ null)。

function coverCandidates(isbn13, knownCover) {
  return [
    knownCover,
    `https://cover.openbd.jp/${isbn13}.jpg`,
    `https://ndlsearch.ndl.go.jp/thumbnail/${isbn13}.jpg`,
  ];
}

function imageLoads(url, timeoutMs) {
  return new Promise((resolve) => {
    const img = new Image();
    // モバイル回線は遅いことがあるため余裕をもって待つ
    const timer = setTimeout(() => { img.src = ''; resolve(false); }, timeoutMs || 10000);
    img.onload = () => {
      clearTimeout(timer);
      resolve(img.naturalWidth > 1 && img.naturalHeight > 1);
    };
    img.onerror = () => { clearTimeout(timer); resolve(false); };
    try { img.referrerPolicy = 'no-referrer'; } catch (e) { /* 未対応でも続行 */ }
    img.src = url;
  });
}

// 候補を並列で確認し、優先順で最初に表示できた URL を返す
async function firstLoadableImage(urls) {
  const list = [];
  for (const raw of urls) {
    const u = httpsCover(raw);
    if (u && list.indexOf(u) < 0) list.push(u);
  }
  for (const u of list) {
    if (u.indexOf('data:') === 0) return u; // 撮影画像はそのまま使える
  }
  if (list.length === 0) return null;
  const results = await Promise.all(list.map((u) => imageLoads(u)));
  for (let i = 0; i < list.length; i++) {
    if (results[i]) return list[i];
  }
  return null;
}

async function resolveCoverUrl(isbn13, knownCover) {
  return firstLoadableImage(coverCandidates(isbn13, knownCover));
}

// 登録済み書籍などの ISBN から表紙を取得する (Google Books の候補も加える)
async function fetchCoverByIsbn(isbn) {
  const isbn13 = toBookIsbn13(isbn);
  if (!isbn13) return null;
  const candidates = coverCandidates(isbn13, null);
  try {
    const g = await fetchGoogleBooks(isbn13);
    if (g && g.cover) candidates.push(g.cover);
  } catch (e) { /* オフライン時などは残りの候補だけ試す */ }
  return firstLoadableImage(candidates);
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

// 「読み取ったらすぐ登録」設定 (既定 ON、選択は端末に保存)
const AUTOREG_KEY = 'bookscope-autoreg';
try {
  $('auto-register').checked = localStorage.getItem(AUTOREG_KEY) !== 'off';
} catch (e) { /* 既定の ON のまま */ }
$('auto-register').addEventListener('change', () => {
  try {
    localStorage.setItem(AUTOREG_KEY, $('auto-register').checked ? 'on' : 'off');
  } catch (e) { /* noop */ }
});

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

  // バーコードを読み取ったら、表紙・内容ごとそのまま登録する
  if ($('auto-register').checked) {
    const ok = await registerBook(book);
    if (ok) markRegistered();
  }
}

// 書籍を 1 冊登録する (成功: true)
async function registerBook(book) {
  try {
    const rec = await store.add(book);
    book.id = rec.id; // 登録直後の表紙変更をそのまま保存できるように控えておく
    if (book.cover) toast(`「${book.title}」を表紙付きで登録しました 📚`);
    else toast(`「${book.title}」を登録しました(表紙は見つかりませんでした)`);
    return true;
  } catch (e) {
    if (e.status === 409) toast('この書籍はすでに登録されています');
    else toast('登録に失敗しました: ' + e.message);
    return false;
  }
}

// 結果カードの登録ボタンを「登録済み」表示にする
function markRegistered() {
  const btn = $('btn-register');
  btn.disabled = true;
  btn.textContent = '✅ 登録済み';
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
    img.src = httpsCover(book.cover);
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
  const btn = $('btn-register');
  btn.disabled = false;
  btn.textContent = '✅ bookscope に登録';
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
  const dataUrl = await chooseCoverImage(currentBook.isbn);
  if (!dataUrl) return;
  currentBook.cover = dataUrl;
  const registered = !!currentBook.id;
  showResult(currentBook);
  if (registered) {
    // すでに登録済み (自動登録直後など) ならそのまま保存する
    markRegistered();
    try {
      await store.update(currentBook.id, { cover: dataUrl });
      toast('表紙画像を更新しました');
    } catch (e) {
      toast('表紙の保存に失敗しました: ' + e.message);
    }
  } else {
    toast('表紙画像を設定しました(登録ボタンで保存されます)');
  }
});

$('btn-register').addEventListener('click', async () => {
  if (!currentBook) return;
  const btn = $('btn-register');
  btn.disabled = true;
  const ok = await registerBook(currentBook);
  if (ok) hideResult();
  else btn.disabled = false;
});

// ---------------- 蔵書一覧 ----------------

let allBooks = [];

// この冊数以上登録されたら、自動的に「表紙だけのギャラリー表示」に切り替える
const GALLERY_MIN_BOOKS = 10;
const VIEW_KEY = 'bookscope-view';

function loadViewPref() {
  try {
    const v = localStorage.getItem(VIEW_KEY);
    return v === 'list' || v === 'gallery' ? v : 'auto';
  } catch (e) { return 'auto'; }
}
function saveViewPref(v) {
  try { localStorage.setItem(VIEW_KEY, v); } catch (e) { /* 保存できなくても動作は継続 */ }
}

let viewPref = loadViewPref();

function currentViewMode() {
  if (viewPref === 'list' || viewPref === 'gallery') return viewPref;
  return allBooks.length >= GALLERY_MIN_BOOKS ? 'gallery' : 'list';
}

// ワンタップで「一覧表 ⇔ 表紙ギャラリー」を切り替えるボタン
$('btn-view-toggle').addEventListener('click', () => {
  viewPref = currentViewMode() === 'gallery' ? 'list' : 'gallery';
  saveViewPref(viewPref);
  renderList();
});

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

// 表紙のない書籍 (ISBN あり) の表紙を、まとめてバーコードの ISBN から取得する
$('btn-fetch-covers').addEventListener('click', async () => {
  const targets = allBooks.filter((b) => !b.cover && toBookIsbn13(b.isbn));
  if (targets.length === 0) {
    toast('表紙のない書籍(ISBN あり)はありません');
    return;
  }
  const btn = $('btn-fetch-covers');
  btn.disabled = true;
  let done = 0;
  let found = 0;
  try {
    for (const b of targets) {
      done++;
      $('list-count').textContent = `表紙を取得中… ${done}/${targets.length} 冊`;
      const url = await fetchCoverByIsbn(b.isbn);
      if (url) {
        await store.update(b.id, { cover: url });
        found++;
      }
    }
    toast(`${targets.length} 冊中 ${found} 冊の表紙を取得しました`);
  } catch (e) {
    toast('表紙の取得中にエラーが発生しました: ' + e.message);
  } finally {
    btn.disabled = false;
  }
  refreshList();
});

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
  const mode = currentViewMode();
  $('list-count').textContent = `${books.length} 冊 / 全 ${allBooks.length} 冊`;
  $('list-empty').hidden = allBooks.length > 0;

  const tableWrap = document.querySelector('.table-wrap');
  const cards = $('book-cards');
  const gallery = $('book-gallery');
  tableWrap.hidden = mode !== 'list';
  cards.hidden = mode !== 'list';
  gallery.hidden = mode !== 'gallery';
  $('btn-view-toggle').textContent =
    mode === 'gallery' ? '📋 一覧表示にする' : '🖼 表紙表示にする';

  if (mode === 'gallery') {
    gallery.textContent = '';
    for (const b of books) gallery.append(galleryTile(b));
    return;
  }

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
  cards.textContent = '';
  for (const b of books) cards.append(bookCard(b));
}

// ---------------- 表紙ギャラリー表示 ----------------

// 表紙タイル。ポイント (ホバー) で内容の概要をその場に表示し、
// タップ/クリックで詳細を開く。
function galleryTile(b) {
  const tile = document.createElement('div');
  tile.className = 'gallery-item';
  tile.tabIndex = 0;

  if (b.cover) {
    const img = document.createElement('img');
    img.loading = 'lazy';
    img.src = httpsCover(b.cover);
    img.alt = b.title || '表紙';
    tile.append(img);
  } else {
    const ph = document.createElement('div');
    ph.className = 'gallery-placeholder';
    ph.textContent = b.title || '(タイトルなし)';
    tile.append(ph);
  }

  const info = document.createElement('div');
  info.className = 'hover-info';
  const t = document.createElement('p');
  t.className = 'hi-title';
  t.textContent = b.title || '';
  info.append(t);
  if (b.author) {
    const a = document.createElement('p');
    a.textContent = b.author;
    info.append(a);
  }
  if (b.description) {
    const d = document.createElement('p');
    d.textContent = b.description;
    info.append(d);
  }
  tile.append(info);

  const open = () => showBookDetail(b);
  tile.addEventListener('click', open);
  tile.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(); }
  });
  return tile;
}

// 書籍の詳細 (表紙・書誌情報・内容) を表示する
let detailBook = null;

function showBookDetail(b) {
  detailBook = b;
  $('detail-title').textContent = b.title || '';
  $('detail-author').textContent = b.author ? `著者: ${b.author}` : '';
  $('detail-publisher').textContent = [b.publisher, b.pubdate].filter(Boolean).join(' / ');
  $('detail-isbn').textContent = b.isbn ? `ISBN: ${b.isbn}` : '';
  $('detail-desc').textContent = b.description || '(内容の概要は登録されていません)';

  const img = $('detail-cover');
  const noCover = $('detail-no-cover');
  if (b.cover) {
    img.src = httpsCover(b.cover);
    img.hidden = false;
    noCover.style.display = 'none';
  } else {
    img.hidden = true;
    noCover.style.display = 'flex';
  }
  $('book-detail').hidden = false;
}

function hideBookDetail() {
  $('book-detail').hidden = true;
  detailBook = null;
}

$('btn-detail-close').addEventListener('click', hideBookDetail);
$('book-detail').addEventListener('click', (ev) => {
  if (ev.target === $('book-detail')) hideBookDetail(); // 背景タップで閉じる
});
$('btn-detail-cover').addEventListener('click', () => {
  if (!detailBook) return;
  const b = detailBook;
  hideBookDetail();
  changeCover(b);
});
$('btn-detail-delete').addEventListener('click', () => {
  if (!detailBook) return;
  const b = detailBook;
  hideBookDetail();
  deleteBook(b);
});

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
    img.src = httpsCover(b.cover);
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
    img.src = httpsCover(b.cover);
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
  const dataUrl = await chooseCoverImage(b.isbn);
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
