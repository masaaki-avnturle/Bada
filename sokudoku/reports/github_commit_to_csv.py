#!/usr/bin/env python3
"""
Usage examples:
  python3 github_commits_to_csv.py --owner someuser --repo somerepo --path tuplenotwork --out commits.csv
  python3 github_commits_to_csv.py -o owner -r repo -p tuplenotwork -t YOUR_GITHUB_TOKEN
"""
import csv
import argparse
import requests

GITHUB_API = "https://api.github.com"

def fetch_commits(owner, repo, path, token=None):
    commits = []
    session = requests.Session()
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    session.headers.update(headers)

    per_page = 100
    page = 1
    while True:
        params = {'path': path, 'per_page': per_page, 'page': page}
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
        resp = session.get(url, params=params)
        if resp.status_code != 200:
            raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")
        page_items = resp.json()
        if not page_items:
            break
        for item in page_items:
            sha = item.get('sha')
            commit = item.get('commit', {})
            author = commit.get('author', {}) or {}
            name = author.get('name') or item.get('author', {}).get('login') or ''
            date = author.get('date', '')
            message = commit.get('message', '').replace('\r', '\\r').replace('\n', '\\n')
            html_url = item.get('html_url', '')
            commits.append({
                'sha': sha,
                'author': name,
                'date': date,
                'message': message,
                'url': html_url
            })
        if len(page_items) < per_page:
            break
        page += 1
    return commits

def write_csv(commits, out_path):
    fieldnames = ['sha', 'author', 'date', 'message', 'url']
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in commits:
            writer.writerow(c)

def main():
    p = argparse.ArgumentParser(description='Fetch commits for a folder on GitHub and save to CSV.')
    p.add_argument('--owner', '-o', required=True, help='GitHub repository owner (user or org)')
    p.add_argument('--repo', '-r', required=True, help='GitHub repository name')
    p.add_argument('--path', '-p', required=True, help='Path in repo to filter commits (e.g. tuplenotwork or tuplenotwork/pdf/)')
    p.add_argument('--out', default='commits.csv', help='Output CSV file (default: commits.csv)')
    p.add_argument('--token', '-t', default=None, help='GitHub personal access token (optional)')
    args = p.parse_args()

    commits = fetch_commits(args.owner, args.repo, args.path, token=args.token)
    write_csv(commits, args.out)
    print(f"Wrote {len(commits)} commits to {args.out}")

if __name__ == '__main__':
    main()
