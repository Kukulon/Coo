import requests
import pandas as pd
import os

def send_telegram_document(token, chat_id, file_path, caption=""):
    """
    發送 Telegram Bot 檔案與訊息通知
    """
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    data = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    try:
        # 將儲存好的 CSV 檔案讀取並放入 payload 中
        with open(file_path, "rb") as f:
            files = {"document": f}
            response = requests.post(url, data=data, files=files)
            response.raise_for_status()
        print("✅ Telegram 檔案與通知推播成功！")
    except Exception as e:
        print(f"❌ Telegram 推播失敗: {e}")

def fetch_twse_openapi(endpoint, target_stocks=None, auto_mode=False):
    """從證交所 OpenAPI 獲取指定端點的資料"""
    base_url = "https://openapi.twse.com.tw/v1"
    url = f"{base_url}{endpoint}"
    
    print(f"正在從證交所抓取資料: {url} ...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        
        data = response.json()
        df = pd.DataFrame(data)
        
        if df.empty:
            print("警告：API 回傳的資料為空。可能是今天尚未結算或無資料。")
            return None, None
            
        print(f"✅ 成功獲取資料！總共取得 {len(df)} 筆紀錄。")
        print("-" * 50)
        
        code_column = None
        possible_code_names = ['公司代號', 'Code', '出表代號', '證券代號']
        for col in possible_code_names:
            if col in df.columns:
                code_column = col
                break
                
        # 1. 三大法人買賣超日報
        if endpoint == "/fund/T86_ALL":
            col_mapping = {
                code_column: '代號',
                'Name': '名稱',
                'ForeignInvestorBuingAndSelling': '外資買賣超',
                'InvestmentTrustNetBuySell': '投信買賣超',
                'DifferenceInNetBuyingAndSelling': '三大法人合計'
            }
            existing_cols = {k: v for k, v in col_mapping.items() if k in df.columns}
            df = df[list(existing_cols.keys())].rename(columns=existing_cols)
            code_column = '代號'
            
            numeric_cols = ['外資買賣超', '投信買賣超', '三大法人合計']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce') // 1000
                    df = df.rename(columns={col: f"{col}(張)"})
                    
        # 2. 融資融券餘額
        elif endpoint == "/exchangeReport/MI_MARGN":
            col_mapping = {
                code_column: '代號', 'Name': '名稱',
                'MarginPurchase': '融資買進', 'MarginSales': '融資賣出', 'MarginBalance': '融資餘額',
                'ShortCovering': '融券買進回補', 'ShortSale': '融券賣出', 'ShortBalance': '融券餘額'
            }
            existing_cols = {k: v for k, v in col_mapping.items() if k in df.columns}
            df = df[list(existing_cols.keys())].rename(columns=existing_cols)
            code_column = '代號'
            
            numeric_cols = ['融資買進', '融資賣出', '融資餘額', '融券買進回補', '融券賣出', '融券餘額']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

        final_df = df.copy()
        
        # --- 進行資料過濾 ---
        if target_stocks and code_column:
            stock_codes = list(target_stocks.keys())
            final_df[code_column] = final_df[code_column].astype(str) 
            filtered_df = final_df[final_df[code_column].isin(stock_codes)].copy()
            
            if filtered_df.empty:
                print(f"在這次的資料中，沒有找到我們關注的股票。")
                return None, None
            else:
                filtered_df['產業分類/概念'] = filtered_df[code_column].map(target_stocks)
                print(f"🎯 找到 {len(filtered_df)} 筆關注的股票資料：")
                final_df = filtered_df 
        else:
            print("未設定過濾清單或找不到代號欄位。")
            
        # --- 自動匯出 CSV 檔案 ---
        default_filename = "twse_data.csv"
        if "T86_ALL" in endpoint: 
            default_filename = "三大法人買賣超.csv"
        elif "MI_MARGN" in endpoint: 
            default_filename = "融資融券餘額.csv"
            
        try:
            final_df.to_csv(default_filename, index=False, encoding='utf-8-sig')
            print(f"💾 太棒了！資料已自動儲存至 '{default_filename}'。")
        except Exception as e:
            print(f"❌ 儲存 CSV 時發生未知的錯誤: {e}")
            return final_df, None
                    
        return final_df, default_filename
                
    except requests.exceptions.SSLError:
        print("❌ SSL 連線錯誤：請檢查公司防火牆。")
    except Exception as e:
        print(f"❌ 資料抓取或處理失敗: {e}")
    return None, None

if __name__ == "__main__":
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
    
    # 檢查是否有設定 Telegram 的環境變數 (代表現在是在 GitHub Actions 或雲端執行)
    tg_token = os.environ.get("TG_TOKEN")
    tg_chat_id = os.environ.get("TG_CHAT_ID")
    
    if tg_token and tg_chat_id:
        print("🤖 偵測到雲端排程環境，啟動自動推播模式...")
        
        # 自動模式下，我們固定抓取三大法人資料來推播
        target_endpoint = "/fund/T86_ALL"
        df, file_path = fetch_twse_openapi(target_endpoint, my_watchlist, auto_mode=True)
        
        if df is not None and not df.empty:
            # 將 DataFrame 轉換為適合 Telegram 閱讀的手機版文字格式 (支援 HTML 加粗標籤)
            tg_msg = "<b>📊 今日籌碼雷達：三大法人買賣超(張)</b>\n" + "="*20 + "\n"
            
            for index, row in df.iterrows():
                f_buy = row.get('外資買賣超(張)', 0)
                t_buy = row.get('投信買賣超(張)', 0)
                # 使用簡單的圖示標註買賣狀態
                f_icon = "🔴買" if f_buy > 0 else "🟢賣" if f_buy < 0 else "平"
                t_icon = "🔴買" if t_buy > 0 else "🟢賣" if t_buy < 0 else "平"
                
                tg_msg += f"🔹 <b>{row['代號']} {row['名稱']}</b>\n"
                tg_msg += f"   外資: {f_buy} {f_icon}\n"
                tg_msg += f"   投信: {t_buy} {t_icon}\n"
                tg_msg += "-"*20 + "\n"
                
            if file_path:
                # 把訊息當作檔案的標題 (caption) 隨著 CSV 一起傳送出去
                send_telegram_document(tg_token, tg_chat_id, file_path, caption=tg_msg)
            
    else:
        # 🌟 電腦本地端執行：直接查詢三大法人買賣超
        print("\n" + "="*50)
        print("📊 台股籌碼監控雷達 (本地互動模式) - 三大法人買賣超")
        print("="*50 + "\n")
        
        target_endpoint = "/fund/T86_ALL" 
        
        fetch_twse_openapi(target_endpoint, my_watchlist, auto_mode=False)
