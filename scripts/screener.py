import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures

def get_russell_2000_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        tables = pd.read_html(url)
        df = tables[2] 
        tickers = df['Ticker'].tolist()
        return [t.replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"List fetch error: {e}")
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY"]

def process_stock(symbol):
    """個別の財務分析を高速化するための並列処理用関数"""
    try:
        stock = yf.Ticker(symbol)
        # 財務諸表を取得（ここが一番時間がかかる）
        fin = stock.financials
        if 'Total Revenue' not in fin.index or len(fin.columns) < 2:
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
            
        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Growth": f"{growth:.2%}",
            "PSR": f"{info.get('priceToSalesTrailing12Months', 0):.2f}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${info.get('currentPrice', 0)}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
target_tickers = all_tickers[:1000] # 1000社に設定

print(f"Starting High-Speed Scan for {len(target_tickers)} stocks...")

found_stocks = []
# ThreadPoolExecutorで並列処理を実行（速度を数倍にアップ）
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_stock, target_tickers))

found_stocks = [r for r in results if r is not None]

df = pd.DataFrame(found_stocks)

# --- TradingView リンク生成 (確実に開く形式) ---
def make_tv_links(symbol):
    # 検索リダイレクトを利用した最も安全なリンク
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
    <title>Tenbagger Hunter 1000</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f9fafb; }}
        .container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        h1 {{ color: #1e40af; border-left: 5px solid #1e40af; padding-left: 15px; font-size: 24px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #edf2f7; text-align: left; }}
        th {{ background: #f8fafc; color: #475569; }}
        tr:hover {{ background: #f1f5f9; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; display: inline-block; }}
        .detail {{ background: #1e40af; color: white; }}
        .chart {{ border: 1px solid #1e40af; color: #1e40af; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Russell 1000 High-Speed Screener</h1>
        <p style="font-size: 12px; color: #64748b;">Last Update: {update_time} (UTC) | 1000 Tickers Scanned</p>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>No results found.</p>"}
        </div>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Scan complete. Found {len(df)} candidates.")
