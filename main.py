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

# 2. 全ページを巡回してスクレイピング
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

saved_count = 0
seen_names = set()
page = 1

print("Googleの全GitHubリポジトリの取得を開始します...")

while True:
    url = f"https://github.com/orgs/google/repositories?page={page}"
    print(f"ページ {page} を取得中...")

    time.sleep(1)  # 課題要件：各アクセス前に1秒待機

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"ページ {page} の取得に失敗したため、処理を終了します。")
        break

    soup = BeautifulSoup(response.text, 'html.parser')
    repos = soup.select('li, div.Box-row, article, div[data-filterable-for]')

    page_saved = 0
    for repo in repos:
        name_tag = repo.select_one('a[itemprop="name codeRepository"], a.Link--primary, h3 a')
        if not name_tag:
            continue

        repo_name = name_tag.text.strip()
        if not repo_name or repo_name in seen_names:
            continue
        seen_names.add(repo_name)

        # 主要言語
        lang_tag = repo.select_one('span[itemprop="programmingLanguage"], [aria-label*="language"]')
        language = lang_tag.text.strip() if lang_tag else "N/A"

        # スター数
        star_tag = repo.select_one('a[href$="/stargazers"], a[href*="/stargazers"]')
        stars = star_tag.text.strip() if star_tag else "0"

        cursor.execute('''
        INSERT INTO google_repos (repo_name, language, stars)
        VALUES (?, ?, ?)
        ''', (repo_name, language, stars))
        page_saved += 1
        saved_count += 1

    conn.commit()

    # 次のページヘのボタンが存在しない、または新しく取得できたリポジトリがない場合は終了
    next_button = soup.select_one('a.next_page, a[rel="next"]')
    if page_saved == 0 or not next_button:
        break

    page += 1

print(f"\n全ページの取得が完了しました！（合計 {saved_count} 件）\n")

# 3. SELECT文で保存したデータを取得して画面表示
print("=== SELECT文による取得結果 ===")
cursor.execute("SELECT repo_name, language, stars FROM google_repos")
rows = cursor.fetchall()

for row in rows:
    print(f"リポジトリ名: {row[0]} | 言語: {row[1]} | スター数: {row[2]}")

conn.close()