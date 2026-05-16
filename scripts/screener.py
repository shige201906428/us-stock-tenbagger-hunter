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
        
        # --- 超緩和版スクリーニング条件 ---
        
        # 1. 時価総額 ($50M - $5.0B)
        # かなり小さなマイクロキャップから、中堅までカバー
        mcap = info.get('marketCap', 0)
        if not (50_000_000 <= mcap <= 5_000_000_000):
            return None

        # 2. 売上高成長率 (5%以上に大幅緩和)
        financials = stock.financials
        growth_display = "N/A"
        if 'Total Revenue' in financials.index and len(financials.columns) >= 2:
            rev = financials.loc['Total Revenue']
            growth = (rev.iloc[0] / rev.iloc[1]) - 1
            if growth < 0.05: # わずかでも成長していればOK
                return None
            growth_display = f"{growth:.2%}"
        else:
            return None
            
        # 3. 株価 ($1以上)
        price = info.get('currentPrice', 0)
        if price < 1.0:
            return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Sector": info.get('sector', 'N/A'),
            "Growth": growth_display,
            "PSR": f"{info.get('priceToSalesTrailing12Months', 0):.2f}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${price}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
# 500社スキャン（ Actionsの制限時間内で最大効率を狙います）
target_tickers = all_tickers[:500]

found_stocks = []
print(f"Wide scanning {len(target_tickers)} companies...")

for i, ticker in enumerate(target_tickers):
    result = check_tenbagger_potential(ticker)
    if result:
        found_stocks.append(result)
        print(f"Found: {ticker}")
    
    if i % 15 == 0:
        time.sleep(0.2)

df = pd.DataFrame(found_stocks)

# --- HTML生成 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Wide Range Hunter</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background-color: #fcfcfc; }}
        .container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }}
        h1 {{ color: #8e44ad; border-bottom: 2px solid #8e44ad; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #f0f0f0; text-align: left; }}
        th {{ background-color: #8e44ad; color: white; }}
        tr:hover {{ background-color: #f5f0f9; }}
        .symbol {{ font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>米国株 広域スクリーナー (Russell 2000 超緩和版)</h1>
        <p style="color:#7f8c8d;">更新日時: {update_time} (UTC) | 条件: $50M-$5B / 成長 5%↑ / $1↑</p>
        {df.to_html(index=False, escape=False) if not df.empty else "<p>該当なし</p>"}
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Wide scan completed.")
