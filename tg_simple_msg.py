import os
import requests

def send_simple_message():
    """
    讀取環境變數中的 Token 與 Chat ID，並發送一段簡單的測試訊息。
    """
    # 從 GitHub Actions 的環境變數中讀取密鑰
    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")

    if not token or not chat_id:
        print("❌ 找不到 TG_TOKEN 或 TG_CHAT_ID 環境變數，請確認 GitHub Secrets 設定！")
        return

    # Telegram 發送訊息的 API URL
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 準備發送的資料載荷
    data = {
        "chat_id": chat_id,
        "text": "👋 <b>嗨！</b>\n這是一則來自 GitHub Actions 的自動化測試訊息！\n\n如果您收到這則訊息，代表您的 <code>TG_TOKEN</code> 與 <code>TG_CHAT_ID</code> 設定完全正確喔！🚀",
        "parse_mode": "HTML"
    }

    try:
        # 發送 POST 請求
        response = requests.post(url, data=data)
        response.raise_for_status() # 檢查是否有 HTTP 錯誤
        print("✅ 測試訊息發送成功！快去 Telegram 看看吧！")
    except Exception as e:
        print(f"❌ 測試訊息發送失敗: {e}")

if __name__ == "__main__":
    print("啟動 Telegram 推播測試...")
    send_simple_message()
