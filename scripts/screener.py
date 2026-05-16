import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures
import time

def get_russell_2000_tickers():
    """WikipediaからRussell 2000の全リストを取得"""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        tables = pd.read_html(url)
        df = tables[2] 
        tickers = df['Ticker'].tolist()
        # 稀にある「.」を含むティッカー（BRK.Bなど）をYahoo Finance形式に変換
        return [str(t).replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"List fetch error: {e}")
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]

def process_stock(symbol):
    """個別の財務分析（2000社対応・超高速版）"""
    try:
        stock = yf.Ticker(symbol)
        
        # 1. 財務諸表を取得（売上成長率の計算用）
        # 過去2年分あれば十分なので軽量化
        fin = stock.get_financials(year=2) 
        if fin.empty or 'Total Revenue' not in fin.index or len(fin.columns) < 2:
            return None
        
        rev = fin.loc['Total Revenue']
        growth = (rev.iloc[0] / rev.iloc[1]) - 1
        
        # 条件: 成長率 5%以上
        if growth < 0.05:
            return None

        # 2. 基本情報を取得
        info = stock.info
        mcap = info.get('marketCap', 0)
        
        # 条件: 時価総額 $50M - $5B (10バガー候補のスイートスポット)
        if not (50_000_000 <= mcap <= 5_000_000_000):
            return None
            
        price = info.get('currentPrice', 0)
        if price < 1.0: # ペニーストック除外
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
# 2000社すべてをターゲットに設定
target_tickers = all_tickers 

print(f"🚀 Starting Full-Scale Scan for {len(target_tickers)} stocks...")
start_time = time.time()

found_stocks = []
# 並列数を増やして一気に処理
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(process_stock, target_tickers))

found_stocks = [r for r in results if r is not None]
df = pd.DataFrame(found_stocks)

print(f"Scan took {time.time() - start_time:.1f} seconds.")

# --- TradingView リンク生成 ---
def make_tv_links(symbol):
    ov_url = f"https://www.tradingview.com/symbols/{symbol}/"
    ct_url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    return (f'<a href="{ov_url}" target="_blank" class="tv-btn detail">Detail</a> '
            f'<a href="{ct_url}" target="_blank" class="tv-btn chart">📈</a>')

if not df.empty:
    df.insert(0, 'TradingView', df['Symbol'].apply(make_tv_links))

# --- HTML出力 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Russell 2000 Full Hunter</title>
    <style>
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; color: #1a202c; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
        h1 {{ color: #2563eb; font-size: 28px; margin-bottom: 5px; }}
        .meta {{ font-size: 13px; color: #64748b; margin-bottom: 25px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 15px; border-bottom: 1px solid #edf2f7; text-align: left; font-size: 14px; }}
        th {{ background: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
        tr:hover {{ background: #f1f5f9; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 5px 10px; border-radius: 6px; font-size: 12px; display: inline-block; transition: 0.2s; }}
        .detail {{ background: #2563eb; color: white; }}
        .chart {{ border: 1px solid #2563eb; color: #2563eb; margin-left: 5px; }}
        .detail:hover {{ background: #1d4ed8; }}
        .chart:hover {{ background: #2563eb; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Russell 2000 Full-Scale Hunter</h1>
        <div class="meta">Last Update: {update_time} (UTC) | Targets: {len(target_tickers)} stocks | Matches: {len(found_stocks)}</div>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>No potential candidates identified in this scan.</p>"}
        </div>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Full Scan Complete. Results saved to {index_path}")
