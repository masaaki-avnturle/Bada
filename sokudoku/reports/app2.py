以下は、ローカルで動かせる簡易Webアプリのサンプルです。特徴は以下のとおりです。
- 左カラム：ファイル履歴（保存ごとに `.history/` にスナップショットを作成）
- 中央：テキストエディタ（CodeMirror を使用し、Vim キーバインドを有効化して「vimっぽく」操作可能）
- 右：ローカルディレクトリのファイルブラウザ（新規作成・編集・保存が可能）
- Python + Flask を使い、ローカルディレクトリを直接読み書きします（実行するPC上でのみ動作）

注意：ブラウザ内で本物の端末 Vim を実行するには wasm/vim のような追加コンポーネントが必要ですが、このサンプルは CodeMirror の Vim キーマップで「vim ライクな体験」を提供します。

使い方（短く）
1. 下のファイルを作成：`app.py` と `templates/index.html`
2. 必要パッケージをインストール：`pip install flask`
3. 実行：`python app.py`
4. ブラウザで `http://127.0.0.1:5000/` を開く

--- ファイル: app.py ---
```python
import os
import io
import time
from flask import Flask, send_from_directory, render_template, jsonify, request, abort

BASE_DIR = os.path.abspath('.')  # 操作対象のローカルディレクトリ（カレント）
HISTORY_DIR = os.path.join(BASE_DIR, '.history')
os.makedirs(HISTORY_DIR, exist_ok=True)

app = Flask(__name__, static_folder='static', template_folder='templates')

def safe_path(rel):
    # 単純な安全対策：BASE_DIR 配下に限定
    target = os.path.abspath(os.path.join(BASE_DIR, rel))
    if not target.startswith(BASE_DIR):
        raise ValueError("invalid path")
    return target

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/list')
def api_list():
    # ファイルツリー（シンプル：ファイルのみリスト）
    files = []
    for root, dirs, filenames in os.walk(BASE_DIR):
        # .history と templates/static 等は除外
        relroot = os.path.relpath(root, BASE_DIR)
        if relroot.startswith('.history') or relroot.startswith('templates') or relroot.startswith('static'):
            continue
        for f in filenames:
            # exclude this script and virtual env files
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
    with io.open(target, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    return jsonify({'path': path, 'content': content})

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
    # create directories if needed
    os.makedirs(os.path.dirname(target), exist_ok=True)
    # write file
    with io.open(target, 'w', encoding='utf-8') as f:
        f.write(content)
    # save history snapshot
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    safe_rel = path.replace(os.sep, '_') or 'root'
    hist_name = f"{timestamp}--{safe_rel}"
    hist_path = os.path.join(HISTORY_DIR, hist_name)
    with io.open(hist_path, 'w', encoding='utf-8') as hf:
        hf.write(content)
    return jsonify({'ok': True})

@app.route('/api/history')
def api_history():
    # .history の一覧
    entries = []
    for name in sorted(os.listdir(HISTORY_DIR), reverse=True):
        p = os.path.join(HISTORY_DIR, name)
        if os.path.isfile(p):
            mtime = os.path.getmtime(p)
            entries.append({'name': name, 'mtime': mtime})
    return jsonify(entries)

@app.route('/api/history/read')
def api_history_read():
    name = request.args.get('name', '')
    p = os.path.join(HISTORY_DIR, name)
    if not os.path.isfile(p):
        return abort(404)
    with io.open(p, 'r', encoding='utf-8', errors='replace') as f:
        return jsonify({'name': name, 'content': f.read()})

# static files (if you want to serve additional local static)
@app.route('/static/<path:p>')
def static_files(p):
    return send_from_directory('static', p)

if __name__ == '__main__':
    app.run(debug=True)
```

--- ファイル: templates/index.html ---
```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>ローカル擬似ホームページ（エディタ付き）</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.6.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.css">
  <style>
    html,body {height:100%;}
    .pane {height:100vh; overflow:auto; padding:8px;}
    #left {background:#f8f9fa;}
    #center {background:#ffffff;}
    #right {background:#f1f3f5;}
    .file-item {cursor:pointer; padding:4px;}
    .file-item:hover {background:#e9ecef;}
    .topbar {padding:6px;}
    #editor {height:70vh; border:1px solid #ddd;}
  </style>
</head>
<body>
  <div class="container-fluid">
    <div class="row topbar">
      <div class="col">
        <h5>ローカル擬似ホーム</h5>
      </div>
    </div>
    <div class="row no-gutters">
      <div id="left" class="col-3 pane">
        <h6>履歴</h6>
        <div id="historyList"></div>
      </div>
      <div id="center" class="col-6 pane">
        <h6>エディタ (Vim キー: Esc + : など、CodeMirror の Vim モード)</h6>
        <div>
          <input id="currentPath" class="form-control" placeholder="ファイルパス（相対）" />
          <div id="editor"></div>
          <div class="mt-2">
            <button id="saveBtn" class="btn btn-primary">保存</button>
            <button id="loadBtn" class="btn btn-secondary">読み込み</button>
          </div>
        </div>
      </div>
      <div id="right" class="col-3 pane">
        <h6>ファイルブラウザ</h6>
        <div>
          <button id="refreshFiles" class="btn btn-sm btn-outline-secondary mb-2">更新</button>
          <button id="newFile" class="btn btn-sm btn-outline-primary mb-2">新規作成</button>
        </div>
        <div id="fileList"></div>
      </div>
    </div>
  </div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/mode/javascript/javascript.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/mode/xml/xml.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/keymap/vim.min.js"></script>
  <script>
    let editor = CodeMirror(document.getElementById('editor'), {
        value: "// ファイルを選択して読み込み、編集して保存してください\n",
        lineNumbers: true,
        mode: "javascript",
        keyMap: "vim", // Vim キーを有効にする
        showCursorWhenSelecting: true,
    });

    function fetchJSON(url) {
      return fetch(url).then(r => {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      });
    }

    function refreshFiles(){
      fetchJSON('/api/list').then(files=>{
        const el = document.getElementById('fileList');
        el.innerHTML = '';
        files.forEach(f=>{
          const div = document.createElement('div');
          div.className = 'file-item';
          div.textContent = f;
          div.onclick = ()=> {
            document.getElementById('currentPath').value = f;
            loadFile(f);
          };
          el.appendChild(div);
        });
      });
    }

    function refreshHistory(){
      fetchJSON('/api/history').then(entries=>{
        const el = document.getElementById('historyList');
        el.innerHTML = '';
        entries.forEach(e=>{
          const d = document.createElement('div');
          d.className = 'file-item';
          d.textContent = e.name;
          d.onclick = ()=>{
            fetchJSON('/api/history/read?name=' + encodeURIComponent(e.name)).then(r=>{
              editor.setValue(r.content);
              document.getElementById('currentPath').value = ''; // 履歴表示
            });
          };
          el.appendChild(d);
        });
      });
    }

    function loadFile(path){
      fetchJSON('/api/read?path=' + encodeURIComponent(path)).then(r=>{
        editor.setValue(r.content);
        // 簡易モード判定：拡張子で言語を切り替える
        if (path.match(/\.html?$/)) editor.setOption('mode','xml');
        else if (path.match(/\.js$/)) editor.setOption('mode','javascript');
        else editor.setOption('mode','text/plain');
      }).catch(err=>{
        alert('読み込み失敗: '+err);
      });
    }

    document.getElementById('refreshFiles').onclick = ()=>{ refreshFiles(); refreshHistory(); };
    document.getElementById('newFile').onclick = ()=>{
      const name = prompt('新規ファイル名（相対パス）を入力:');
      if (name) {
        document.getElementById('currentPath').value = name;
        editor.setValue('');
      }
    };
    document.getElementById('loadBtn').onclick = ()=>{
      const p = document.getElementById('currentPath').value;
      if (p) loadFile(p);
      else alert('ファイルパスを入力してください');
    };
    document.getElementById('saveBtn').onclick = ()=>{
      const p = document.getElementById('currentPath').value;
      if (!p) { alert('ファイルパスを入力してください'); return; }
      fetch('/api/save', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
        body: JSON.stringify({path: p, content: editor.getValue()})
      }).then(r=>{
        if (!r.ok) throw new Error('save failed');
        return r.json();
      }).then(()=> {
        alert('保存しました');
        refreshFiles();
        refreshHistory();
      }).catch(e=>{
        alert('保存失敗: ' + e);
      });
    };

    // 初期読み込み
    refreshFiles();
    refreshHistory();
  </script>
</body>
</html>
```

これで、ローカルディレクトリを読み書きでき、中央に Vim ライクなエディタ、左に保存履歴（.history）、右にファイルブラウザがある簡易的なホームページ風インターフェースが動きます。必要なら本物の wasm-vim を組み込む方法や権限設定、セキュリティ対策についても補足します。どの部分を拡張したいですか？
