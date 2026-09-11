#!/usr/bin/env node
/*
 * bookscope server
 *
 * 依存パッケージなしで動く Node.js サーバー。
 *  - public/ 以下の静的ファイル配信(スキャン画面・蔵書一覧画面)
 *  - /api/books の REST API(蔵書データは data/books.json に保存)
 *
 * スマホ・タブレットのカメラ(getUserMedia)は HTTPS か localhost でしか
 * 動かないため、certs/server.key と certs/server.crt を置くと HTTPS でも
 * 待ち受ける。作り方は README.md を参照。
 */
'use strict';

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = Number(process.env.PORT || 3000);
const HTTPS_PORT = Number(process.env.HTTPS_PORT || 3443);
const ROOT = __dirname;
const PUBLIC_DIR = path.join(ROOT, 'public');
const DATA_DIR = path.join(ROOT, 'data');
const DATA_FILE = path.join(DATA_DIR, 'books.json');
const CERT_KEY = path.join(ROOT, 'certs', 'server.key');
const CERT_CRT = path.join(ROOT, 'certs', 'server.crt');
const MAX_BODY = 1024 * 1024; // 1MB

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
};

// ---------- 蔵書データの読み書き ----------

function loadBooks() {
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    return [];
  }
}

function saveBooks(books) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  const tmp = DATA_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(books, null, 2));
  fs.renameSync(tmp, DATA_FILE);
}

// ---------- ユーティリティ ----------

function sendJson(res, status, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > MAX_BODY) {
        reject(new Error('body too large'));
        req.destroy();
        return;
      }
      chunks.push(c);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

function normalizeIsbn(isbn) {
  return String(isbn || '').replace(/[^0-9Xx]/g, '').toUpperCase();
}

// ---------- API ----------

async function handleApi(req, res, pathname) {
  // GET /api/books : 全件取得
  if (pathname === '/api/books' && req.method === 'GET') {
    sendJson(res, 200, loadBooks());
    return;
  }

  // POST /api/books : 1冊登録
  if (pathname === '/api/books' && req.method === 'POST') {
    let payload;
    try {
      payload = JSON.parse(await readBody(req));
    } catch (e) {
      sendJson(res, 400, { error: 'invalid JSON body' });
      return;
    }
    const isbn = normalizeIsbn(payload.isbn);
    const title = String(payload.title || '').trim();
    if (!title && !isbn) {
      sendJson(res, 400, { error: 'title または isbn が必要です' });
      return;
    }
    const books = loadBooks();
    if (isbn && books.some((b) => b.isbn === isbn)) {
      sendJson(res, 409, { error: 'この ISBN は登録済みです', isbn });
      return;
    }
    const book = {
      id: crypto.randomUUID(),
      isbn,
      title,
      author: String(payload.author || '').trim(),
      publisher: String(payload.publisher || '').trim(),
      pubdate: String(payload.pubdate || '').trim(),
      cover: String(payload.cover || '').trim(),
      description: String(payload.description || '').trim(),
      registeredAt: new Date().toISOString(),
    };
    books.push(book);
    saveBooks(books);
    sendJson(res, 201, book);
    return;
  }

  // DELETE /api/books/:id : 1冊削除
  const delMatch = pathname.match(/^\/api\/books\/([0-9a-f-]+)$/i);
  if (delMatch && req.method === 'DELETE') {
    const id = delMatch[1];
    const books = loadBooks();
    const next = books.filter((b) => b.id !== id);
    if (next.length === books.length) {
      sendJson(res, 404, { error: 'not found' });
      return;
    }
    saveBooks(next);
    sendJson(res, 200, { ok: true });
    return;
  }

  sendJson(res, 404, { error: 'not found' });
}

// ---------- 静的ファイル ----------

function serveStatic(req, res, pathname) {
  let rel = decodeURIComponent(pathname);
  if (rel === '/') rel = '/index.html';
  const filePath = path.normalize(path.join(PUBLIC_DIR, rel));
  if (!filePath.startsWith(PUBLIC_DIR + path.sep) && filePath !== PUBLIC_DIR) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not Found');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

// ---------- サーバー起動 ----------

async function handler(req, res) {
  const url = new URL(req.url, 'http://localhost');
  const pathname = url.pathname;
  try {
    if (pathname.startsWith('/api/')) {
      await handleApi(req, res, pathname);
    } else if (req.method === 'GET' || req.method === 'HEAD') {
      serveStatic(req, res, pathname);
    } else {
      res.writeHead(405);
      res.end('Method Not Allowed');
    }
  } catch (e) {
    console.error(e);
    if (!res.headersSent) sendJson(res, 500, { error: 'internal error' });
  }
}

http.createServer(handler).listen(PORT, () => {
  console.log(`bookscope: http://localhost:${PORT}`);
  console.log('  (カメラを使う場合、スマホ・タブレットからは HTTPS が必要です)');
});

if (fs.existsSync(CERT_KEY) && fs.existsSync(CERT_CRT)) {
  const options = {
    key: fs.readFileSync(CERT_KEY),
    cert: fs.readFileSync(CERT_CRT),
  };
  https.createServer(options, handler).listen(HTTPS_PORT, () => {
    console.log(`bookscope: https://<このPCのIPアドレス>:${HTTPS_PORT} (スマホ・タブレット用)`);
  });
} else {
  console.log('  certs/server.key, certs/server.crt を置くと HTTPS でも起動します (README.md 参照)');
}
