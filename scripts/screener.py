import yfinance as yf
import pandas as pd
from datetime import datetime
import os
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
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
# 2000社からランダムに1000社抽出
target_tickers = random.sample(all_tickers, min(len(all_tickers), 1000))

print(f"--- Start Processing {len(target_tickers)} tickers ---")

# 高速化のため一括でデータをダウンロード（ここがポイント！）
# 1000社分のinfoを一気に取得しようとするとエラーが出やすいため、100社ずつのグループに分ける
group_size = 100
found_stocks = []
processed_count = 0

for i in range(0, len(target_tickers), group_size):
    group = target_tickers[i:i+group_size]
    print(f"Processing group: {i} to {i+group_size}...")
    
    for symbol in group:
        processed_count += 1
        try:
            stock = yf.Ticker(symbol)
            # infoの取得。失敗したら次へ
            info = stock.info
            if not info: continue

            # 時価総額チェック（上限 $5B）
            mcap = info.get('marketCap', 0)
            if mcap > 5_000_000_000 or mcap == 0: continue

            # 成長率チェック (infoから優先、なければ飛ばす)
            growth = info.get('revenueGrowth')
            if growth is None or growth <= 0: continue

            found_stocks.append({
                "Symbol": symbol,
                "Name": info.get('shortName', 'N/A'),
                "Sector": info.get('sector', 'N/A'),
                "Growth": f"{growth:.2%}",
                "PSR": f"{info.get('priceToSalesTrailing12Months', 0):.2f}",
                "MarketCap": f"${mcap/1e6:.1f}M",
                "Price": f"${info.get('currentPrice', 0)}"
            })
        except:
            continue

print(f"--- Finished! Processed: {processed_count}, Matches: {len(found_stocks)} ---")

# --- HTML出力（TradingViewリンク含む） ---
df = pd.DataFrame(found_stocks)
if not df.empty:
    df.insert(0, 'TradingView', df['Symbol'].apply(lambda x: 
        f'<a href="https://www.tradingview.com/symbols/{x}/" target="_blank" class="tv-btn detail">Detail</a> '
        f'<a href="https://www.tradingview.com/chart/?symbol={x}" target="_blank" class="tv-btn chart">📈</a>'
    ))

update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Daily Hunter 1000</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; display: inline-block; }}
        .detail {{ background: #0d6efd; color: white; }}
        .chart {{ border: 1px solid #0d6efd; color: #0d6efd; margin-left: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #dee2e6; text-align: left; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 Daily Hunter (1,000 Scan)</h1>
        <p>Last Update: {update_time} (UTC) | Scanned: {processed_count} | Found: {len(found_stocks)}</p>
        {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found.</p>"}
    </div>
</body>
</html>
"""

# 保存処理（省略：これまでのコードと同じ）
current_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(current_dir, "..", "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)
