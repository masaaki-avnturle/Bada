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
