# 在這裡定義你的「數位眼線」監控池
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

# Telegram 配置
    tg_token = os.environ.get("TG_TOKEN")
    tg_chat_id = os.environ.get("TG_CHAT_ID")

# Define the new endpoint URL as requested by the user
target_endpoint_url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"

# 獲取並處理資料 (using the renamed generic function)
df_result, file_path = fetch_and_process_twse_data(target_endpoint_url, my_watchlist)

if df_result is not None and not df_result.empty:
    # Generate a generic table string for the Telegram message
    # Add a title based on the endpoint
    endpoint_name = os.path.basename(target_endpoint_url.split('?')[0]).replace('_', ' ').strip().upper()
    tg_msg = f"<b>📊 TWSE 報告: {endpoint_name}</b>\n" + "="*30 + "\n"

    # Use to_string() to get a formatted table representation
    # Limiting rows to avoid very long messages, maybe first 10 rows
    table_str = df_result.head(10).to_string(index=False)
    if len(df_result) > 10:
        table_str += f"\n... (顯示前 10 筆資料，共 {len(df_result)} 筆)"

    tg_msg += f"<pre>{table_str}</pre>\n" # Use <pre> for monospaced font in Telegram

    if file_path:
        # 把訊息當作檔案的標題 (caption) 隨著 CSV 一起傳送出去
        send_telegram_document(tg_token, tg_chat_id, file_path, caption=tg_msg)
else:
    print("❌ 未能獲取或處理資料，不發送 Telegram 通知。")
