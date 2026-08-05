import os
import requests
from bs4 import BeautifulSoup

# --- 設定項目 ---
# 監視対象のURL
TARGET_URL = "https://example-hospital.or.jp/recruit/pharmacist"  # 対象の病院求人ページURLに変更
# 検知したいキーワード（複数該当で判定）
KEYWORDS = ["薬剤師", "募集", "中途"]

# 環境変数からLINEのキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

STATE_FILE = "last_state.txt"

def send_line_notification(message):
    """LINE Messaging APIを使ってプッシュメッセージを送信"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        print("LINE通知を送信しました。")
    else:
        print(f"LINE通知エラー: {res.status_code}, {res.text}")

def check_website():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"Webサイトの取得に失敗しました: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    # 不要なタグを除外して本文抽出
    for element in soup(["script", "style", "nav", "footer"]):
        element.extract()
    text_content = soup.get_text()

    # キーワードチェック
    found_keywords = [kw for kw in KEYWORDS if kw in text_content]
    
    # 前回の結果を読み込む
    last_state = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            last_state = f.read().strip()

    # 現状の状態文字列（キーワードが含まれているか＋簡単なテキスト長）
    current_state = f"Keywords:{','.join(found_keywords)}_Len:{len(text_content)}"

    print(f"前回の状態: {last_state}")
    print(f"今回の状態: {current_state}")

    # 変更検知のロジック
    if last_state != "" and current_state != last_state:
        # キーワードが含まれている場合のみ通知
        if "薬剤師" in found_keywords:
            msg = f"【求人更新の可能性あり】\n対象ページに変化を検知しました。\n\n検出キーワード: {', '.join(found_keywords)}\nURL: {TARGET_URL}"
            send_line_notification(msg)

    # 状態の保存
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(current_state)

if __name__ == "__main__":
    check_website()
