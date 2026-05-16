import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import time

def get_russell_2000_tickers():
    """
    WikipediaからRussell 2000のリストを取得
    """
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
    """
    超緩和スクリーニングロジック
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 1. 時価総額 ($50M - $5.0B)
        mcap = info.get('marketCap', 0)
        if not (50_000_000 <= mcap <= 5_000_000_000):
            return None

        # 2. 売上高成長率 (5%以上)
        financials = stock.financials
        growth_val = 0
        if 'Total Revenue' in financials.index and len(financials.columns) >= 2:
            rev = financials.loc['Total Revenue']
            growth_val = (rev.iloc[0] / rev.iloc[1]) - 1
            if growth_val < 0.05: 
                return None
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
            "Growth": f"{growth_val:.2%}",
            "PSR": f"{info.get('priceToSalesTrailing12Months', 0):.2f}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${price}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
# Actionsの実行時間を考慮し、500社をスキャン
target_tickers = all_tickers[:500]

found_stocks = []
print(f"Scanning {len(target_tickers)} Russell 2000 companies...")

for i, ticker in enumerate(target_tickers):
    result = check_tenbagger_potential(ticker)
    if result:
        found_stocks.append(result)
    if i % 15 == 0:
        time.sleep(0.2)

df = pd.DataFrame(found_stocks)

# --- TradingViewリンク化ロジック ---
def make_tv_link(symbol):
    # 万能なチャートリンク形式
    url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    return f'<a href="{url}" target="_blank" class="tv-link">{symbol}</a>'

if not df.empty:
    df['Symbol'] = df['Symbol'].apply(make_tv_link)

# --- HTML生成 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tenbagger Hunter Pro</title>
    <style>
        body {{ font-family: 'Inter', -apple-system, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; color: #333; }}
        .container {{ max-width: 1100px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
        h1 {{ color: #2962ff; font-size: 24px; margin-bottom: 5px; display: flex; align-items: center; }}
        .update-time {{ color: #666; font-size: 13px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 15px; border-bottom: 1px solid #eee; text-align: left; }}
        th {{ background-color: #f8f9fb; color: #555; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
        tr:hover {{ background-color: #f0f7ff; }}
        .tv-link {{ 
            color: #2962ff; 
            text-decoration: none; 
            font-weight: bold; 
            padding: 2px 6px; 
            border-radius: 4px; 
            border: 1px solid #2962ff;
        }}
        .tv-link:hover {{ background-color: #2962ff; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 米国株 10倍株スクリーナー</h1>
        <p class="update-time">最終更新(UTC): {update_time} | スキャン対象: Russell 2000 (上位500社)</p>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>条件に合う銘柄は見つかりませんでした。</p>"}
        </div>
        <p style="margin-top:20px; font-size:11px; color:#999;">
            条件: $50M-$5B / 成長率5%↑ / 価格$1↑ / リンク先: TradingView
        </p>
    </div>
</body>
</html>
"""

# 保存先（リポジトリのルートへ）
current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Complete! Found {len(df)} candidates.")
