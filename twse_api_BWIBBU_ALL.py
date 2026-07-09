import os
import requests
import pandas as pd
import datetime

# ==========================================
# 1. 定義共用函式 (這就是你原本遺失的部分)
# ==========================================

def fetch_and_process_twse_data(api_url, watchlist):
    """
    向證交所 API 抓取資料，過濾出關注清單，並存成 CSV 檔案。
    """
    print(f"開始抓取資料: {api_url}")
    try:
        # 加上 Headers 模擬瀏覽器，降低被阻擋的機率
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            print("⚠ API 回傳空資料。")
            return None, None

        # 將 JSON 轉為 Pandas DataFrame
        df = pd.DataFrame(data)

        # 確保有 'Code' 欄位可用於比對 (不同 API 欄位名稱可能不同，做個簡單防護)
        if 'Code' not in df.columns and '證券代號' in df.columns:
            df = df.rename(columns={'證券代號': 'Code', '證券名稱': 'Name'})

        # 只保留監控清單內的股票
        target_codes = list(watchlist.keys())
        df['Code'] = df['Code'].astype(str) # 確保型別為字串
        df_filtered = df[df['Code'].isin(target_codes)].copy()

        if df_filtered.empty:
            print("⚠ 監控清單內的股票今日無資料。")
            return df_filtered, None

        # 匯出成 CSV 檔案 (使用 utf-8-sig 讓 Excel 打開不會亂碼)
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        file_path = f"twse_report_{date_str}.csv"
        df_filtered.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"✅ 資料處理完成，已儲存至 {file_path}")

        return df_filtered, file_path

    except Exception as e:
        print(f"❌ 抓取或處理資料時發生錯誤: {e}")
        return None, None

def send_telegram_document(token, chat_id, document_path, caption):
    """
    透過 Telegram Bot API 傳送檔案與文字訊息。
    """
    print("準備發送 Telegram 訊息...")
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    
    try:
        with open(document_path, 'rb') as file:
            files = {'document': file}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'HTML' # 允許使用 HTML 標籤排版
            }
            response = requests.post(url, data=data, files=files)
            
            # 如果發送失敗，印出 Telegram API 的詳細錯誤訊息以便除錯
            if response.status_code != 200:
                print(f"❌ Telegram API 錯誤: {response.text}")
            else:
                print("✅ Telegram 訊息與檔案發送成功！")
                
    except Exception as e:
        print(f"❌ 傳送 Telegram 時發生例外錯誤: {e}")

# ==========================================
# 2. 主程式邏輯與參數設定
# ==========================================

# 在這裡定義你的「數位眼線」監控池
my_watchlist = {
    '6719': '力智 (高階DrMOS)',
    '6435': '大中 (MOSFET)',
    '2308': '台達電 (HDVC電源)',
    '3324': '雙鴻 (散熱)',
    '3630': '星通 (網通/機器人相關)',
    '2454': '聯發科',
    '2330': '台積電',
    '2305': '全友',
    '3189': '景碩',
    '3551': '世禾',
    '6285': '啟碁',
    '8299': '群聯'
}

# 讀取 GitHub Secrets 環境變數
tg_token = os.environ.get("TG_TOKEN") 
tg_chat_id = os.environ.get("TG_CHAT_ID")

# 安全檢查：確保環境變數有抓到
if not tg_token or not tg_chat_id:
    raise ValueError("❌ 找不到 TG_TOKEN 或 TG_CHAT_ID！請確認 GitHub Secrets 是否已正確設定。")

# 設定要呼叫的 API 網址
target_endpoint_url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"

# 執行抓取與處理
df_result, file_path = fetch_and_process_twse_data(target_endpoint_url, my_watchlist)

# 如果有資料，準備排版並發送
if df_result is not None and not df_result.empty:
    endpoint_name = os.path.basename(target_endpoint_url.split('?')[0]).replace('_', ' ').strip().upper()
    tg_msg = f"<b>📊 TWSE 報告: {endpoint_name}</b>\n" + "="*30 + "\n"

    # 將表格轉為文字 (限制前 10 筆)
    table_str_raw = df_result.head(10).to_string(index=False)
    
    # 避免 Telegram Caption 超過 1024 字元限制
    max_caption_length = 900 

    if len(table_str_raw) > max_caption_length:
        table_str = table_str_raw[:max_caption_length] + "\n... (內容過長已截斷)"
    else:
        table_str = table_str_raw

    if len(df_result) > 10:
        table_str += f"\n... (顯示前 10 筆資料，共 {len(df_result)} 筆)"

    # 使用 <pre> 標籤等寬字體排版
    tg_msg += f"<pre>{table_str}</pre>\n" 

    if file_path:
        # 再次確保總字數不超過 Telegram 限制
        final_caption = tg_msg
        if len(final_caption) > 1020: 
            final_caption = final_caption[:1017] + "..."

        # 呼叫發送函式
        send_telegram_document(tg_token, tg_chat_id, file_path, caption=final_caption)
else:
    print("❌ 未能獲取或處理資料，不發送 Telegram 通知。")
