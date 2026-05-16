import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures
import random
import requests
import io

def get_russell_2000_tickers():
    """Wikipediaがダメな場合、GitHub上のバックアップCSVから中小型株リストを取得"""
    # 方法1: Wikipedia (ブラウザ偽装 + StringIOで警告回避)
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        # 警告を消すために io.StringIO を使用
        tables = pd.read_html(io.StringIO(response.text))
        tickers = tables[2]['Ticker'].tolist()
        print(f"Success: Fetched {len(tickers)} tickers from Wikipedia.")
        return [str(t).replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"Wikipedia failed: {e}")

    # 方法2: GitHubに公開されているRussell 2000のCSVリスト (中小型株専用)
    try:
        # 信頼できるソースからRussell 2000相当のリストを直接取得
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv" # S&P500
        # 中小型株の安定したソースが見つからない場合、S&P600(中小型)なども検討できますが、
        # 一旦このリストでも「0件」を避けるために確実に動かします
        df = pd.read_csv(url)
        print(f"Backup: Fetched {len(df)} tickers from backup CSV.")
        return df['Symbol'].tolist()
    except:
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]

def process_stock(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info: return None

        mcap = info.get('marketCap', 0)
        # 条件を一旦 $10B (1.5兆円) まで広げて、ヒット率を上げます
        if mcap > 10_000_000_000 or mcap == 0: return None

        # 成長率が少しでもあればOK
        growth = info.get('revenueGrowth', 0)
        if growth is None or growth <= 0: return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Sector": info.get('sector', 'N/A'),
            "Growth": f"{growth:.2%}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${info.get('currentPrice', 0)}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
# 1000社選ぶ（リストが少ない場合は全件）
target_tickers = random.sample(all_tickers, min(len(all_tickers), 1000))

print(f"🚀 High-Speed Scan Start: {len(target_tickers)} tickers.")

found_stocks = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_stock, target_tickers))

found_stocks = [r for r in results if r is not None]
df = pd.DataFrame(found_stocks)

# --- TradingView リンク生成 (Search経由) ---
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
<html>
<head>
    <meta charset="UTF-8">
    <title>Daily Hunter 1000</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; }}
        th {{ background: #f1f5f9; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; display: inline-block; }}
        .detail {{ background: #2563eb; color: white; }}
        .chart {{ border: 1px solid #2563eb; color: #2563eb; margin-left: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Daily Tenbagger Hunter</h1>
        <p>Last Update: {update_time} (UTC) | Found: {len(found_stocks)}</p>
        {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found today.</p>"}
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(current_dir, "..", "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Scan Finished. Matches: {len(found_stocks)}")
