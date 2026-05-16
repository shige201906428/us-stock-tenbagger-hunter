import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures
import random
import requests
import io

def get_russell_2000_tickers():
    """Wikipediaを第一候補、ダメならGitHubからS&P 600(小型株)を取得"""
    # 1. Wikipedia (User-Agentを最新のブラウザに似せる)
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=15)
        tables = pd.read_html(io.StringIO(response.text))
        tickers = tables[2]['Ticker'].tolist()
        print(f"Success: Fetched {len(tickers)} tickers from Wikipedia.")
        return [str(t).replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"Wikipedia failed (will use backup): {e}")

    # 2. 予備：GitHub上のS&P 600 (小型株リスト)
    # Wikipediaがダメでも、ここから600社の小型株を確実に取得できます
    try:
        url = "https://raw.githubusercontent.com/datasets/s-and-p-600-companies/master/data/constituents.csv"
        df = pd.read_csv(url)
        print(f"Backup Success: Fetched {len(df)} Small-Cap tickers from S&P 600 list.")
        return df['Symbol'].tolist()
    except:
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]

def process_stock(symbol):
    try:
        # 通信の安定性を高めるため、個別のリクエストに短い待機を入れる
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info: return None

        # --- 10バガー条件 ---
        mcap = info.get('marketCap', 0)
        # 時価総額 $50M - $5B (中小型株のスイートスポット)
        if not (50_000_000 <= mcap <= 5_000_000_000): return None

        # 売上成長率がプラス
        growth = info.get('revenueGrowth', 0)
        if growth is None or growth <= 0: return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Sector": info.get('sector', 'N/A'),
            "Growth": f"{growth:.2%}",
            "PSR": f"{info.get('priceToSalesTrailing12Months', 0):.2f}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${info.get('currentPrice', 0)}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
# 毎日新鮮な1000社をスキャン
target_tickers = random.sample(all_tickers, min(len(all_tickers), 1000))

print(f"🚀 High-Speed Scan Start: {len(target_tickers)} tickers selected.")

found_stocks = []
# 並列数を15に増やしてさらに高速化
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

# --- HTML出力 (デザインをさらにプロ仕様に) ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tenbagger Hunter 1000</title>
    <style>
        body {{ font-family: 'Inter', -apple-system, sans-serif; margin: 0; padding: 20px; background: #f3f4f6; color: #1f2937; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); }}
        h1 {{ color: #1d4ed8; font-size: 28px; letter-spacing: -0.025em; }}
        .meta {{ font-size: 13px; color: #6b7280; margin-bottom: 25px; border-bottom: 1px solid #e5e7eb; padding-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 15px; border-bottom: 1px solid #f3f4f6; text-align: left; }}
        th {{ background: #f9fafb; color: #4b5563; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
        tr:hover {{ background: #eff6ff; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 5px 10px; border-radius: 6px; font-size: 11px; display: inline-block; }}
        .detail {{ background: #1d4ed8; color: white; }}
        .chart {{ border: 1px solid #1d4ed8; color: #1d4ed8; margin-left: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Tenbagger Hunter 1000</h1>
        <div class="meta">Last Update: {update_time} (UTC) | Scanned: {len(target_tickers)} | Found: {len(found_stocks)}</div>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found in today's sample.</p>"}
        </div>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(current_dir, "..", "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Update Complete. Found: {len(found_stocks)}")
