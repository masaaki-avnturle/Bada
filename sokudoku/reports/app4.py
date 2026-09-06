以下は、WASM版のVim（事前にビルドした Emscripten / wasm モジュール）を組み込み、実用的なホームページ／エディタ環境として動作する最小実装例です。ポイントは次の通りです。

- サーバー側：Flask（Python）でファイルの一覧取得・読み書き・履歴保存を行うAPIと静的配布を担当。
- クライアント側：xterm.js をターミナル表示に使い、事前ビルド済みの Vim WASM（`static/wasm/vim.js` と `static/wasm/vim.wasm` を想定）をロードして標準入出力を xterm に接続。ファイルの読み書きはサーバーAPI経由。
- 重要：ここで使う WASM バイナリ／Glue (`vim.wasm` / `vim.js`) はユーザー側でビルドまたは入手してください（neovim-wasm / wasm-vim 等のプロジェクトを参照）。下のコードはそのモジュールが Emscripten の「Module」スタイルで stdin/stdout/stderr を hook できることを前提にしています。

セットアップ（要約）
1. このファイル群を同一ディレクトリに置く（`app.py`, `templates/index.html`, `static/`）。
2. `static/wasm/` に事前ビルドした `vim.js` と `vim.wasm` を置く。`vim.js` は Emscripten の glue JS。
3. 必要パッケージをインストール：`pip install flask`
4. 実行：`python app.py`
5. ブラウザで `http://127.0.0.1:5000/` を開く

注意点
- セキュリティ：このサンプルは開発用途向けです。公開サーバーで使うと任意ファイルの読み書きを許すため危険です。
- WASMビルド：実際に動かすには Vim/Neovim を WASM 用にビルドし、Emscripten 出力で `Module` を通して stdin/stdout を利用できる形にする必要があります（プロジェクトごとに手順が異なります）。

ファイル：app.py
```python
import os, io, time
from flask import Flask, render_template, jsonify, request, abort, send_from_directory

BASE_DIR = os.path.abspath('.')  # 操作対象ディレクトリ（カレント）
HISTORY_DIR = os.path.join(BASE_DIR, '.history')
os.makedirs(HISTORY_DIR, exist_ok=True)

app = Flask(__name__, template_folder='templates', static_folder='static')

def safe_path(rel):
    target = os.path.abspath(os.path.join(BASE_DIR, rel))
    if not target.startswith(BASE_DIR):
        raise ValueError("invalid path")
    return target

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/list')
def api_list():
    files = []
    for root, dirs, filenames in os.walk(BASE_DIR):
        relroot = os.path.relpath(root, BASE_DIR)
        if relroot.startswith('.history') or relroot.startswith('static') or relroot.startswith('templates'):
            continue
        for f in filenames:
            if f == os.path.basename(__file__):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, BASE_DIR)
            files.append(rel)
    return jsonify(sorted(files))

@app.route('/api/read')
def api_read():
    path = request.args.get('path', '')
    try:
        target = safe_path(path)
    except ValueError:
        return abort(400)
    if not os.path.isfile(target):
        return abort(404)
    with io.open(target, 'r', encoding='utf-8', errors='replace') as fh:
        return jsonify({'path': path, 'content': fh.read()})

@app.route('/api/save', methods=['POST'])
def api_save():
    data = request.json
    if not data:
        return abort(400)
    path = data.get('path', '')
    content = data.get('content', '')
    try:
        target = safe_path(path)
    except ValueError:
        return abort(400)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with io.open(target, 'w', encoding='utf-8') as fh:
        fh.write(content)
    ts = time.strftime('%Y%m%d-%H%M%S')
    hist_name = f"{ts}--{path.replace(os.sep,'_') or 'root'}"
    with io.open(os.path.join(HISTORY_DIR, hist_name), 'w', encoding='utf-8') as hf:
        hf.write(content)
    return jsonify({'ok': True})

@app.route('/api/history')
def api_history():
    entries = []
    for name in sorted(os.listdir(HISTORY_DIR), reverse=True):
        p = os.path.join(HISTORY_DIR, name)
        if os.path.isfile(p):
            entries.append({'name': name, 'mtime': os.path.getmtime(p)})
    return jsonify(entries)

@app.route('/api/history/read')
def api_history_read():
    name = request.args.get('name', '')
    p = os.path.join(HISTORY_DIR, name)
    if not os.path.isfile(p):
        return abort(404)
    with io.open(p, 'r', encoding='utf-8', errors='replace') as f:
        return jsonify({'name': name, 'content': f.read()})

# 静的な WASM / glue JS を配布するルート（通常 Flask の static で十分）
@app.route('/wasm/<path:p>')
def wasm_files(p):
    return send_from_directory(os.path.join(app.static_folder, 'wasm'), p)

if __name__ == '__main__':
    app.run(debug=True)
```

ファイル：templates/index.html
```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>実用ホーム + WASM Vim</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@4.20.0/css/xterm.css">
  <style>
    html,body {height:100%;}
    .pane {height:100vh; overflow:auto; padding:8px;}
    #left {background:#f8f9fa;}
    #center {background:#ffffff;}
    #right {background:#f1f3f5;}
    #terminal {height:70vh; border:1px solid #ccc; background:black;}
    .file-item {cursor:pointer; padding:4px;}
    .file-item:hover {background:#e9ecef;}
  </style>
</head>
<body>
  <div class="container-fluid">
    <div class="row topbar py-2">
      <div class="col"><h5>実用ホーム + WASM Vim</h5></div>
    </div>
    <div class="row no-gutters">
      <div id="left" class="col-3 pane">
        <h6>ファイル一覧</h6>
        <div id="fileList"></div>
        <div class="mt-2">
          <button id="refreshFiles" class="btn btn-sm btn-outline-secondary">更新</button>
        </div>
      </div>

      <div id="center" class="col-6 pane">
        <h6>WASM Vim ターミナル</h6>
        <div id="terminal"></div>
        <div class="mt-2">
          <small>注意: Vim の保存は Vim 内で :w を使うか、外部 API を叩く連携ボタンで行えます。</small>
        </div>
        <div class="mt-2">
          <button id="loadToVim" class="btn btn-primary btn-sm">選択ファイルを Vim にロード</button>
          <button id="saveFromVim" class="btn btn-success btn-sm">Vim から保存（読み取り）</button>
        </div>
      </div>

      <div id="right" class="col-3 pane">
        <h6>履歴</h6>
        <div id="historyList"></div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/xterm@4.20.0/lib/xterm.js"></script>
  <script>
    // 前提: static/wasm/vim.js と vim.wasm が存在し、Emscripten Module 形式で stdin/stdout を hook 可能
    // 簡易的な接続例を示します。実際の glue API に合わせて調整してください。

    let term = new window.Terminal({cols: 100, rows: 30});
    term.open(document.getElementById('terminal'));

    // 仮の Module 作成 — Emscripten glue が global scope に ModuleFactory を公開する場合などに合わせてください。
    // ここでは fetch して wasm を instantiate する低レイヤー例も示しますが、実際には vim.js に従ってください.

    // stdin buffer
    const inputQueue = [];
    function sendToWasmInput(data) {
      // data: string. Emscripten Module の stdin hook に流す実装に合わせてください.
      inputQueue.push(data);
      if (Module && Module.stdinCallback) {
        Module.stdinCallback(data);
      }
    }

    // xterm -> wasm の入力
    term.onData(e => {
      sendToWasmInput(e);
    });

    // 出力を xterm に流すユーティリティ
    function wasmWriteOutput(s) {
      term.write(s);
    }

    // ----- Module のロード（Emscripten glue 使用想定） -----
    // 期待する振る舞い（例）
    //   - global に `createVimModule` のような factory がある場合:
    //     createVimModule({ stdin: fn, stdout: fn, stderr: fn }).then(Module => { ... })
    // ここでは一般的なパターンを想定した「呼び出し箇所」の雛形を示します。

    let Module = null;

    // 実際に使う glue に合わせて以下を置き換えてください。
    async function initWasmVim() {
      // 例: Emscripten が出力した vim.js が `createVimModule` を提供する場合
      if (window.createVimModule) {
        Module = await window.createVimModule({
          stdin: function() {
            if (inputQueue.length === 0) return null;
            const s = inputQueue.shift();
            // Emscripten が期待する数値列で渡す場合は変換が必要
            return s;
          },
          stdout: function(ptr, len) {
            // もし glue がポインタ/len を渡すならメモリから読み取る処理を必要
            // ここでは直接文字列が渡される想定:
            wasmWriteOutput(ptr);
          },
          stderr: function(s) { wasmWriteOutput(s); }
        });
      } else {
        // 代替: 手動で wasm を fetch+instantiate して起動するケース（非常にモジュール依存）
        // 実際には Emscripten 出力の API に従ってください。
        console.warn("createVimModule not found. please provide wasm glue (vim.js) that exposes a factory.");
      }
    }

    // ファイル→Vim ロードのための簡易連携:
    // 方法A: Emscripten FS を使える場合、サーバーから内容を読み、Module.FS.writeFile で仮想FSへ置き、Vim 内で :e /path を実行
    async function loadFileIntoVim(path) {
      const res = await fetch('/api/read?path=' + encodeURIComponent(path));
      if (!res.ok) { alert('read failed'); return; }
      const j = await res.json();
      const content = j.content;
      if (Module && Module.FS) {
        const virtualPath = '/' + path.replace(/\\/g, '/');
        // ensure directories
        const dir = virtualPath.substring(0, virtualPath.lastIndexOf('/')) || '/';
        try { Module.FS.mkdirTree(dir); } catch(e){}
        Module.FS.writeFile(virtualPath, content);
        // Vim コマンドでファイルを開く（Emscripten の callMain / stdin を利用）
        // ここでは簡易的にコマンドを送る:
        sendToWasmInput(':e ' + virtualPath + '\n');
      } else {
        alert('Module.FS not available. Check wasm glue API.');
      }
    }

    // Vim から保存して Python サーバーに反映する簡易フロー:
    // 方法: Module.FS.readFile で仮想FSから取得して /api/save に POST
    async function saveFileFromVim(path) {
      if (!(Module && Module.FS)) { alert('Module.FS not available'); return; }
      try {
        const virtualPath = '/' + path.replace(/\\/g, '/');
        const data = Module.FS.readFile(virtualPath, {encoding: 'utf8'});
        const res = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
          body: JSON.stringify({path: path, content: data})
        });
        if (!res.ok) throw new Error('save failed');
        alert('保存しました: ' + path);
      } catch (e) {
        alert('保存失敗: ' + e);
      }
    }

    // UI 周り: ファイル一覧 / 履歴の取得
    async function refreshFiles(){
      const r = await fetch('/api/list');
      const files = await r.json();
      const el = document.getElementById('fileList');
      el.innerHTML = '';
      files.forEach(f=>{
        const d = document.createElement('div');
        d.className = 'file-item';
        d.textContent = f;
        d.onclick = ()=> { selectFile(f); };
        el.appendChild(d);
      });
    }
    async function refreshHistory(){
      const r = await fetch('/api/history');
      const arr = await r.json();
      const el = document.getElementById('historyList');
      el.innerHTML = '';
      arr.forEach(e=>{
        const d = document.createElement('div');
        d.className = 'file-item';
        d.textContent = e.name;
        el.appendChild(d);
      });
    }

    let selectedFile = null;
    function selectFile(f){ selectedFile = f; Array.from(document.querySelectorAll('.file-item')).forEach(el=>el.style.fontWeight=''); event.target.style.fontWeight='bold'; }

    document.getElementById('refreshFiles').onclick = ()=>{ refreshFiles(); refreshHistory(); };
    document.getElementById('loadToVim').onclick = ()=>{ if (!selectedFile) return alert('ファイルを選択してください'); loadFileIntoVim(selectedFile); };
    document.getElementById('saveFromVim').onclick = ()=>{ if (!selectedFile) return alert('保存先ファイル名を選択してください'); saveFileFromVim(selectedFile); };

    // 初期化
    (async ()=>{
      await initWasmVim();
      refreshFiles();
      refreshHistory();
      term.writeln('WASM Vim ロード待機中...');
    })();
  </script>
</body>
</html>
```

補足（短く）
- 上のクライアントJSは「Emscripten が出力する glue（vim.js）」に依存します。多くの WASM-Vim プロジェクトは ModuleFactory（create...Module）や Module オブジェクト、FS API を提供します。実際の API に合わせて `initWasmVim` / `sendToWasmInput` / stdout の取り扱いを調整してください。
- もし「どのプロジェクトを使ってビルドするか（neovim-wasm 等）」を決めていただければ、該当プロジェクトに合わせたより具体的な接続コード（実例）を提示できます。

まずはこの構成で試してみて、使う WASM Vim のビルド/配布方法（どのリポジトリ・どの出力形式）を教えてください。具体的な glue に合わせてコードを調整します。
