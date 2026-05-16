import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import time

def get_russell_2000_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        tables = pd.read_html(url)
        df = tables[2] 
        tickers = df['Ticker'].tolist()
        return [t.replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"List fetch error: {e}")
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]

def check_tenbagger_potential(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # --- 緩和版スクリーニング条件 ---
        
        # 1. 時価総額 ($100M - $3.0B)
        mcap = info.get('marketCap', 0)
        if not (100_000_000 <= mcap <= 3_000_000_000):
            return None

        # 2. 売上高成長率 (15%以上に緩和)
        financials = stock.financials
        if 'Total Revenue' in financials.index and len(financials.columns) >= 2:
            rev = financials.loc['Total Revenue']
            # 直近と前年の比較
            growth = (rev.iloc[0] / rev.iloc[1]) - 1
            if growth < 0.15: 
                return None
        else:
            return None
            
        # 3. PSR (20倍までに緩和)
        psr = info.get('priceToSalesTrailing12Months', 100)
        if psr > 20: 
            return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Sector": info.get('sector', 'N/A'),
            "Growth": f"{growth:.2%}",
            "PSR": f"{psr:.2f}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${info.get('currentPrice', 0)}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
# 実行時間との兼ね合いで、上位500社をスキャン
target_tickers = all_tickers[:500]

found_stocks = []
print(f"Scanning {len(target_tickers)} Russell 2000 companies with relaxed conditions...")

for i, ticker in enumerate(target_tickers):
    result = check_tenbagger_potential(ticker)
    if result:
        found_stocks.append(result)
        print(f"Match found: {ticker}")
    
    if i % 10 == 0:
        time.sleep(0.3) # サーバー負荷に配慮

df = pd.DataFrame(found_stocks)

# --- HTML生成 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Russell 2000 Hunter - Relaxed</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 30px; background-color: #f8fbfd; }}
        .container {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
        h1 {{ color: #27ae60; border-left: 6px solid #27ae60; padding-left: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 25px; }}
        th, td {{ padding: 12px 15px; border-bottom: 1px solid #eee; text-align: left; }}
        th {{ background-color: #27ae60; color: white; }}
        tr:hover {{ background-color: #f1fef6; }}
        .symbol {{ font-weight: bold; color: #2c3e50; }}
        .update-time {{ font-size: 0.85em; color: #95a5a6; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>米国中小型株スクリーナー (Russell 2000 / 緩和版)</h1>
        <p class="update-time">更新日時: {update_time} (UTC) | 対象: Russell 2000上位500社</p>
        {df.to_html(index=False, escape=False) if not df.empty else "<p>該当なし。条件をさらに調整してください。</p>"}
        <p style="margin-top:20px; font-size:0.8em; color:#bdc3c7;">
            ※条件: 時価総額 $100M-$3B / 売上成長率 15%↑ / PSR 20↓
        </p>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Scan completed successfully.")
