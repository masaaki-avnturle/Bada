import csv
import os
from git import Repo, NULL_TREE
from datetime import datetime

# 設定
REPO_PATH = '.'# スクリプトを置く場所がリポジトリルートならそのまま
TARGET_DIR = 'tuplenetwork'  # 対象フォルダ（リポジトリルートからの相対パス）
TARGET_AUTHOR = 'masaaki'
OUTPUT_CSV = 'comment.csv'

def is_pdf_path(path):
    return path.lower().endswith('.pdf')

def main():
    repo = Repo(REPO_PATH)
    if repo.bare:
        raise RuntimeError('指定パスはベアリポジトリです。')

    rows = []
    seen = set()  # 同じファイル・同じコミット重複を避けるため

    # 全コミットを走査（最新→過去）
    for commit in repo.iter_commits(paths=TARGET_DIR):
        # 作者名でフィルタ
        author_name = commit.author.name
        if author_name != TARGET_AUTHOR:
            continue

        # コミットの差分から変更されたファイルを調べる
        # マージコミット等も含めて安全に差分を取る
        parents = commit.parents
        if parents:
            diffs = commit.diff(parents[0], create_patch=False)
        else:
            # 初回コミット：親がいない場合は差分を against NULL_TREE
            diffs = commit.diff(NULL_TREE)

        commit_dt = datetime.utcfromtimestamp(commit.committed_date).isoformat() + 'Z'
        commit_hash = commit.hexsha
        message = commit.message.strip().splitlines()[0] if commit.message else ''

        for d in diffs:
            # d.a_path / d.b_path のいずれかが対象パス
            path = d.b_path or d.a_path
            if not path:
                continue
            # 先頭に TARGET_DIR/ が含まれていること（サブディレクトリも許容）
            if not (path.startswith(TARGET_DIR + os.sep) or path == TARGET_DIR):
                continue
            if not is_pdf_path(path):
                continue

            key = (path, commit_hash)
            if key in seen:
                continue
            seen.add(key)

            rows.append({
                'path': path,
                'commit_hash': commit_hash,
                'committed_date': commit_dt,
                'author': author_name,
                'message': message,
            })

    # CSV 出力
    fieldnames = ['path', 'commit_hash', 'committed_date', 'author', 'message']
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f'wrote {len(rows)} rows to {OUTPUT_CSV}')

if __name__ == '__main__':
    main()
