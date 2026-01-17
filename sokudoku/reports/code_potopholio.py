以下は、Python（Flask）で実装した2つの簡易ウェブサイトの完全なソースコード例です。どちらも軽量で自己完結しています。実運用向けにはセキュリティ・認証・入力検証・デプロイ設定（HTTPS等）を追加してください。

- サイトA: ソースコードを公開する個人用ホームページ（リポジトリ一覧、各プロジェクトページ、静的ファイルホスティング）
- サイトB: 時々の日記を公開する簡易ブログ（管理者用シンプル認証で記事を追加・編集、Markdown対応）

両方とも Python 3.8+ と Flask が必要です。共通の依存:
pip install flask markdown2

1) ソース公開サイト（code_portfolio）
ファイル構成:
- code_portfolio/
  - app.py
  - templates/
    - index.html
    - project.html
    - base.html
  - static/
    - (任意の静的ファイル: ソースのZIPやreadme等を置けます)
  - data/
    - projects.json

code_portfolio/app.py
```python
#!/usr/bin/env python3
# code_portfolio/app.py
# Simple personal "source code" portfolio site

import os
import json
from flask import Flask, render_template, send_from_directory, abort, url_for

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")

app = Flask(__name__, static_folder=STATIC_DIR)

def load_projects():
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.isfile(PROJECTS_FILE):
        # create sample
        sample = [
            {
                "id": "sample-cli",
                "title": "Sample CLI Tool",
                "description": "A small command-line utility written in Python.",
                "files": ["sample-cli.zip"],
                "tags": ["python", "cli"],
                "readme": "A short README for Sample CLI."
            }
        ]
        with open(PROJECTS_FILE, "w", encoding="utf8") as f:
            json.dump(sample, f, indent=2, ensure_ascii=False)
    with open(PROJECTS_FILE, "r", encoding="utf8") as f:
        return json.load(f)

@app.route("/")
def index():
    projects = load_projects()
    return render_template("index.html", projects=projects)

@app.route("/project/<proj_id>/")
def project_page(proj_id):
    projects = load_projects()
    for p in projects:
        if p.get("id") == proj_id:
            return render_template("project.html", project=p)
    abort(404)

@app.route("/files/<path:filename>")
def files(filename):
    # serve files from static (or another directory). adjust as needed.
    if ".." in filename:
        abort(400)
    return send_from_directory(STATIC_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
```

code_portfolio/data/projects.json (例: 自動生成されるが手動作成も可)
```json
[
  {
      "id": "sample-cli",
      "title": "Sample CLI Tool",
      "description": "A small command-line utility written in Python.",
      "files": ["sample-cli.zip"],
      "tags": ["python", "cli"],
    "readme": "A short README for Sample CLI."
  }
]
```

templates/base.html
```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>{{ title or "My Code Portfolio" }}</title>
    <style>
      body { font-family: Arial, sans-serif; max-width: 900px; margin: 2rem auto; }
      header { margin-bottom: 1rem; }
      nav a { margin-right: 1rem; }
      .project { border-bottom: 1px solid #ddd; padding: .5rem 0; }
      .tags { color: #666; font-size: .9rem; }
    </style>
  </head>
  <body>
    <header>
      <h1><a href="{{ url_for('index') }}">My Code Portfolio</a></h1>
      <nav>
        <a href="{{ url_for('index') }}">Home</a>
      </nav>
    </header>
    {% block content %}{% endblock %}
    <footer style="margin-top:2rem;color:#888;font-size:.9rem;">
      © Your Name
    </footer>
  </body>
</html>
```

templates/index.html
```html
{% extends "base.html" %}
{% block content %}
  <h2>Projects</h2>
  {% for p in projects %}
    <div class="project">
      <h3><a href="{{ url_for('project_page', proj_id=p.id) }}">{{ p.title }}</a></h3>
      <div>{{ p.description }}</div>
      <div class="tags">Tags: {{ p.tags|join(', ') }}</div>
    </div>
  {% endfor %}
{% endblock %}
```

templates/project.html
```html
{% extends "base.html" %}
{% block content %}
  <h2>{{ project.title }}</h2>
  <p>{{ project.description }}</p>
  <h3>Files</h3>
  <ul>
    {% for f in project.files %}
      <li><a href="{{ url_for('files', filename=f) }}">{{ f }}</a></li>
    {% endfor %}
  </ul>
  <h3>Readme</h3>
  <pre>{{ project.readme }}</pre>
{% endblock %}
```

使い方:
- code_portfolio 配下で `pip install flask`、`python app.py` を実行。
- `static/` に配布可能なソースアーカイブやバイナリを置く。
- `data/projects.json` を編集してプロジェクトを追加。

2) 日記サイト（simple_diary）
ファイル構成:
- simple_diary/
  - app.py
  - templates/
    - base.html
    - index.html
    - view.html
    - edit.html
  - posts/  (Markdownファイルを保存: yyyy-mm-dd-title.md)
  - secret_token.txt  (管理者ログイン用のシンプルトークン。実運用では適切な認証を使う)

simple_diary/app.py
```python
#!/usr/bin/env python3
# simple_diary/app.py
# Tiny diary/blog with simple token "auth" for posting (not production-safe).

import os
import datetime
                 from flask import Flask, render_template, request, redirect, url_for, abort, flash, send_from_directory
import markdown2

BASE = os.path.dirname(__file__)
POSTS_DIR = os.path.join(BASE, "posts")
TOKEN_FILE = os.path.join(BASE, "secret_token.txt")

app = Flask(__name__)
app.secret_key = "change-this-secret"  # change for production

def ensure_dirs():
    os.makedirs(POSTS_DIR, exist_ok=True)
    if not os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE, "w", encoding="utf8") as f:
            f.write("changeme")
    with open(TOKEN_FILE, "r", encoding="utf8") as f:
        token = f.read().strip()
    return token

def list_posts():
    files = []
    for name in os.listdir(POSTS_DIR):
        if name.endswith(".md"):
            path = os.path.join(POSTS_DIR, name)
            mtime = os.path.getmtime(path)
            files.append((name, mtime))
    files.sort(key=lambda x: x[1], reverse=True)
    return [n for n,_ in files]

def read_post(filename):
    path = os.path.join(POSTS_DIR, filename)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf8") as f:
        text = f.read()
    html = markdown2.markdown(text)
    title = filename.rsplit(".md",1)[0]
    return {"title": title, "body": html, "raw": text}

@app.route("/")
def index():
    posts = list_posts()
    # display file title prettified
    items = []
    for p in posts:
        title = p[:-3]
        items.append({"file": p, "title": title})
    return render_template("index.html", posts=items)

@app.route("/post/<path:fname>/")
def view_post(fname):
    post = read_post(fname)
    if not post:
        abort(404)
    return render_template("view.html", post=post, filename=fname)

@app.route("/edit/", methods=["GET", "POST"])
def edit_index():
    token = ensure_dirs()
    if request.method == "POST":
        form_token = request.form.get("token","")
        if form_token != token:
            flash("Invalid token")
            return redirect(url_for("edit_index"))
        # creating new post
        title = request.form.get("title","").strip()
        content = request.form.get("content","")
        if not title:
            flash("Title required")
            return redirect(url_for("edit_index"))
        safe_title = "".join(c for c in title if c.isalnum() or c in "-_ ").strip().replace(" ", "-")
        date = datetime.date.today().isoformat()
        filename = f"{date}-{safe_title}.md"
        path = os.path.join(POSTS_DIR, filename)
        with open(path, "w", encoding="utf8") as f:
            f.write(f"# {title}\n\n")
            f.write(content)
        flash("Post created")
        return redirect(url_for("view_post", fname=filename))
    # GET: show edit form
    return render_template("edit.html")

@app.route("/raw/<path:fname>")
def raw_post(fname):
    path = os.path.join(POSTS_DIR, fname)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(POSTS_DIR, fname, as_attachment=False)

if __name__ == "__main__":
    ensure_dirs()
    app.run(host="0.0.0.0", port=8001, debug=True)
```

templates/base.html
```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{{ title or "My Diary" }}</title>
    <style>
      body { font-family: Georgia, serif; max-width: 800px; margin: 2rem auto; }
      header { margin-bottom: 1rem; }
      nav a { margin-right: 1rem; }
      .flash { color: red; }
    </style>
  </head>
  <body>
    <header>
      <h1><a href="{{ url_for('index') }}">My Diary</a></h1>
      <nav>
        <a href="{{ url_for('index') }}">Home</a> |
        <a href="{{ url_for('edit_index') }}">New Post</a>
      </nav>
    </header>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="flash">{% for m in messages %}{{ m }}<br>{% endfor %}</div>
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
    <footer style="margin-top:2rem;color:#888;font-size:.9rem;">
      © Your Name
    </footer>
  </body>
</html>
```

templates/index.html
```html
{% extends "base.html" %}
{% block content %}
  <h2>Entries</h2>
  <ul>
    {% for p in posts %}
      <li><a href="{{ url_for('view_post', fname=p.file) }}">{{ p.title }}</a></li>
    {% else %}
      <li>No posts yet.</li>
    {% endfor %}
  </ul>
                 <p>To create a post, click "New Post" and provide the admin token.</p>
{% endblock %}
```

templates/view.html
```html
{% extends "base.html" %}
{% block content %}
  <article>
    <h2>{{ post.title }}</h2>
    <div>{{ post.body|safe }}</div>
    <p><a href="{{ url_for('raw_post', fname=filename) }}">Download raw markdown</a></p>
  </article>
{% endblock %}
```

templates/edit.html
```html
{% extends "base.html" %}
{% block content %}
  <h2>New Post</h2>
  <form method="post">
    <label>Admin Token: <input type="password" name="token"></label><br><br>
    <label>Title: <input type="text" name="title" style="width:60%"></label><br><br>
    <label>Content (Markdown):</label><br>
    <textarea name="content" rows="20" style="width:100%"></textarea><br>
    <button type="submit">Create</button>
  </form>
{% endblock %}
```

使い方（simple_diary）:
- simple_diary 配下で `pip install flask markdown2`
- 初回実行で `posts/` と `secret_token.txt`（中身 "changeme"）が作られます。`secret_token.txt` を編集して管理用トークンを設定してください。
- 起動: `python app.py`（ポート8001）
- 管理者は「New Post」からトークンを入力して投稿します。

注意（要確認・強調）:
- これらは学習／個人運用目的の簡易実装です。本番公開する場合は、必ず下記を検討してください:
  - HTTPS（TLS）で配信する
  - 強力な認証・CSRF対策・入力検証
  - ファイルアップロード制御（サイズ・拡張子・MIME）
  - 適切なログ・バックアップ・アクセス制御

必要なら、次を追加で提供します:
- Dockerfile / systemd ユニット例
- 本番向け（gunicorn + nginx）構成例
- OAuth/パスワード認証の追加
どれを追加しますか？
