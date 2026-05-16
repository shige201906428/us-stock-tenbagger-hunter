import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures
import random
import requests

def get_russell_2000_tickers():
    """Wikipediaからの取得をブラウザ偽装で実行。ダメなら予備から取得"""
    # 1. Wikipedia (ブラウザのふりをしてアクセス)
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)
        df = tables[2]
        tickers = df['Ticker'].tolist()
        return [str(t).replace('.', '-') for t in tickers if isinstance(t, str)]
    except Exception as e:
        print(f"Wikipedia fetch error: {e}")

    # 2. 予備：外部の安定したCSV（もしWikipediaがダメな場合）
    try:
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
        df = pd.read_csv(url)
        return df['Symbol'].tolist()
    except:
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]

def process_stock(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info: return None

        mcap = info.get('marketCap', 0)
        # 条件：$5.0B以下
        if mcap > 5_000_000_000 or mcap == 0: return None

        # 条件：成長率プラス
        growth = info.get('revenueGrowth', 0)
        if growth is None or growth <= 0: return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Growth": f"{growth:.2%}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${info.get('currentPrice', 0)}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
target_tickers = random.sample(all_tickers, min(len(all_tickers), 1000))

print(f"🚀 High-Speed Scan Start: {len(target_tickers)} tickers selected.")

found_stocks = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_stock, target_tickers))

found_stocks = [r for r in results if r is not None]
df = pd.DataFrame(found_stocks)

# TradingViewリンク生成
def make_tv_links(symbol):
    ov_url = f"https://www.tradingview.com/symbols/{symbol}/"
    ct_url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    return f'<a href="{ov_url}" target="_blank" style="color:#2563eb;font-weight:bold;text-decoration:none;">Detail</a> | <a href="{ct_url}" target="_blank" style="text-decoration:none;">📈</a>'

if not df.empty:
    df.insert(0, 'Links', df['Symbol'].apply(make_tv_links))

# HTML出力
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Daily Hunter 1000</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; font-size: 14px; }}
        th {{ background: #f8fafc; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Daily Tenbagger Hunter (1,000 Scan)</h1>
        <p>Last Update: {update_time} (UTC) | Found: {len(found_stocks)}</p>
        {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found.</p>"}
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(current_dir, "..", "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Scan Finished. Matches: {len(found_stocks)}")
