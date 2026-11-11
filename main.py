import time
import sqlite3
import requests
from bs4 import BeautifulSoup

# 1. データベースの設定とテーブル作成
conn = sqlite3.connect('github_google.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS google_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_name TEXT,
    language TEXT,
    stars TEXT
)
''')

# 毎回実行時にデータをリセット
cursor.execute('DELETE FROM google_repos')
conn.commit()

# 2. スクレイピング処理
url = "https://github.com/orgs/google/repositories"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("GoogleのGitHubページを取得中...")
time.sleep(1)  # 課題要件：必ず1秒待機する

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# リポジトリカードになり得る要素を柔軟に取得
repos = soup.select('li, div.Box-row, article, div[data-filterable-for]')

# 3. データの抽出とデータベース保存
saved_count = 0
seen_names = set()

for repo in repos:
    # リポジトリ名の取得
    name_tag = repo.select_one('a[itemprop="name codeRepository"], a.Link--primary, h3 a')
    if not name_tag:
        continue

    repo_name = name_tag.text.strip()
    if not repo_name or repo_name in seen_names:
        continue
    seen_names.add(repo_name)

    # 主要言語の取得
    lang_tag = repo.select_one('span[itemprop="programmingLanguage"], [aria-label*="language"]')
    language = lang_tag.text.strip() if lang_tag else "N/A"

    # スター数の取得
    star_tag = repo.select_one('a[href$="/stargazers"], a[href*="/stargazers"]')
    stars = star_tag.text.strip() if star_tag else "0"

    cursor.execute('''
    INSERT INTO google_repos (repo_name, language, stars)
    VALUES (?, ?, ?)
    ''', (repo_name, language, stars))
    saved_count += 1

conn.commit()
print(f"データベースへの保存が完了しました！（{saved_count}件）\n")

# 4. SELECT文で保存したデータを取得して画面表示
print("=== SELECT文による取得結果 ===")
cursor.execute("SELECT repo_name, language, stars FROM google_repos")
rows = cursor.fetchall()

for row in rows:
    print(f"リポジトリ名: {row[0]} | 言語: {row[1]} | スター数: {row[2]}")

conn.close()