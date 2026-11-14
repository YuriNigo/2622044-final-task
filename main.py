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
    name_links = soup.select('a[itemprop="name codeRepository"], h3 a, h4 a')

    page_saved = 0
    for name_tag in name_links:
        href = name_tag.get('href', '')
        if not href.startswith('/google/') or href.count('/') != 2:
            continue

        repo_name = name_tag.get_text(strip=True)
        if not repo_name or repo_name in seen_names:
            continue
        seen_names.add(repo_name)

        # リポジトリ1件分のカード要素を取得
        card = name_tag.find_parent('li') or name_tag.find_parent('div', class_='Box-row') or name_tag.parent.parent

        # 主要言語の取得
        language = "N/A"
        lang_tag = card.select_one('span[itemprop="programmingLanguage"]')
        if lang_tag and lang_tag.get_text(strip=True):
            language = lang_tag.get_text(strip=True)
        else:
            color_dot = card.select_one('span.repo-language-color, span[style*="background-color"]')
            if color_dot and color_dot.parent:
                lang_text = color_dot.parent.get_text(strip=True)
                if lang_text:
                    language = lang_text

        # スター数の取得
        star_tag = card.select_one('a[href$="/stargazers"], a[href*="/stargazers"]')
        stars = star_tag.get_text(strip=True) if star_tag else "0"

        cursor.execute('''
        INSERT INTO google_repos (repo_name, language, stars)
        VALUES (?, ?, ?)
        ''', (repo_name, language, stars))
        page_saved += 1
        saved_count += 1

    conn.commit()

    # 次のページが存在しない、または新しく取得できたリポジトリがない場合は終了
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