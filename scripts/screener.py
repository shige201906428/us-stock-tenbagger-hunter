import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures
import random

def get_russell_2000_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        tables = pd.read_html(url)
        df = tables[2] 
        tickers = df['Ticker'].tolist()
        return [str(t).replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"List fetch error: {e}")
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY"]

def process_stock(symbol):
    try:
        stock = yf.Ticker(symbol)
        # 財務データ（軽量取得）
        fin = stock.get_financials(year=2) 
        if fin.empty or 'Total Revenue' not in fin.index or len(fin.columns) < 2:
            return None
        
        rev = fin.loc['Total Revenue']
        growth = (rev.iloc[0] / rev.iloc[1]) - 1
        
        # 条件: 成長率 5%以上
        if growth < 0.05:
            return None

        info = stock.info
        mcap = info.get('marketCap', 0)
        # 条件: 時価総額 $50M - $5B
        if not (50_000_000 <= mcap <= 5_000_000_000):
            return None
            
        price = info.get('currentPrice', 0)
        if price < 1.0:
            return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Sector": info.get('sector', 'N/A'),
            "Growth": f"{growth:.2%}",
            "PSR": f"{info.get('priceToSalesTrailing12Months', 0):.2f}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${price}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()

# ★ここがポイント: 2000社からランダムに1000社を抽出
target_tickers = random.sample(all_tickers, min(len(all_tickers), 1000))

print(f"🎲 Randomly selected {len(target_tickers)} stocks for today's scan.")

found_stocks = []
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    results = list(executor.map(process_stock, target_tickers))

found_stocks = [r for r in results if r is not None]
df = pd.DataFrame(found_stocks)

# --- TradingView リンク生成 ---
def make_tv_links(symbol):
    ov_url = f"https://www.tradingview.com/symbols/{symbol}/"
    ct_url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    return f'<a href="{ov_url}" target="_blank" class="tv-btn detail">Detail</a> <a href="{ct_url}" target="_blank" class="tv-btn chart">📈</a>'

if not df.empty:
    df.insert(0, 'TradingView', df['Symbol'].apply(make_tv_links))

# --- HTML出力 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Daily Random Hunter 1000</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background: #f4f7f6; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ color: #1e293b; font-size: 24px; }}
        .meta {{ font-size: 13px; color: #64748b; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
        th {{ background: #f8fafc; color: #475569; font-size: 12px; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; display: inline-block; }}
        .detail {{ background: #2563eb; color: white; }}
        .chart {{ border: 1px solid #2563eb; color: #2563eb; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 Daily Random Tenbagger Hunter</h1>
        <div class="meta">Last Update: {update_time} (UTC) | Today's Sample: 1,000 / 2,000 stocks</div>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found in today's random sample.</p>"}
        </div>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)
