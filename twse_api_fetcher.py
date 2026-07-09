import os
# 假設你的 fetch_and_process_twse_data, send_telegram_document 等函式都寫在上方或另有 import

# 格式為 { '股票代號': '你給它的產業標籤' }
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

# --- 修改區域開始 ---
# Telegram 配置改由系統環境變數讀取 (對應 GitHub Secrets)
tg_token = os.environ.get("TG_TOKEN") 
tg_chat_id = os.environ.get("TG_CHAT_ID")

# 增加安全防護：如果忘記設定環境變數，直接報錯並停止執行
if not tg_token or not tg_chat_id:
    raise ValueError("❌ 找不到 TG_TOKEN 或 TG_CHAT_ID！請確認 GitHub Secrets 是否已正確設定。")
# --- 修改區域結束 ---

# Define the new endpoint URL as requested by the user
target_endpoint_url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
#https://openapi.twse.com.tw/v1/fund/BFI82U

# 獲取並處理資料 (using the renamed generic function)
df_result, file_path = fetch_and_process_twse_data(target_endpoint_url, my_watchlist)

if df_result is not None and not df_result.empty:
    # Generate a generic table string for the Telegram message
    # Add a title based on the endpoint
    endpoint_name = os.path.basename(target_endpoint_url.split('?')[0]).replace('_', ' ').strip().upper()
    tg_msg = f"<b>📊 TWSE 報告: {endpoint_name}</b>\n" + "="*30 + "\n"

    # Use to_string() to get a formatted table representation
    # Limiting rows to avoid very long messages, maybe first 10 rows
    table_str_raw = df_result.head(10).to_string(index=False)
    
    # Telegram caption limit is typically 1024 characters. 
    # We'll use a slightly smaller limit to be safe and account for HTML tags.
    max_caption_length = 900 # A safe limit for the table string part

    if len(table_str_raw) > max_caption_length:
        table_str = table_str_raw[:max_caption_length] + "\n... (內容過長已截斷)"
    else:
        table_str = table_str_raw

    if len(df_result) > 10:
        table_str += f"\n... (顯示前 10 筆資料，共 {len(df_result)} 筆)"

    tg_msg += f"<pre>{table_str}</pre>\n" # Use <pre> for monospaced font in Telegram

    if file_path:
        # 把訊息當作檔案的標題 (caption) 隨著 CSV 一起傳送出去
        # Ensure the final tg_msg does not exceed Telegram's overall caption limit (1024 chars)
        final_caption = tg_msg
        if len(final_caption) > 1020: # Slightly less than 1024 to be safe
            final_caption = final_caption[:1017] + "..."

        send_telegram_document(tg_token, tg_chat_id, file_path, caption=final_caption)
else:
    print("❌ 未能獲取或處理資料，不發送 Telegram 通知。")
