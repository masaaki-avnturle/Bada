import io
import os
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
