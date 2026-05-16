import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import time

def get_russell_2000_tickers():
    """WikipediaからRussell 2000のリストを取得"""
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
    """超緩和スクリーニングロジック"""
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

# --- TradingView ダブルリンク生成ロジック ---
def make_tv_links(symbol):
    # オーバービューリンク (詳細)
    ov_url = f"https://jp.tradingview.com/symbols/AMEX-{symbol}/"
    # チャートリンク (分析)
    ct_url = f"https://jp.tradingview.com/chart/?symbol={symbol}"
    
    links = (
        f'<a href="{ov_url}" target="_blank" class="tv-btn overview">概要</a> '
        f'<a href="{ct_url}" target="_blank" class="tv-btn chart">📈</a>'
    )
    return links

if not df.empty:
    df.insert(0, 'TradingView', df['Symbol'].apply(make_tv_links))

# --- HTML生成 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tenbagger Hunter Pro Max</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background-color: #f4f7f6; color: #333; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h1 {{ color: #1e293b; font-size: 26px; border-left: 6px solid #2563eb; padding-left: 15px; }}
        .update-time {{ color: #64748b; font-size: 13px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
        th {{ background-color: #f8fafc; color: #475569; font-weight: 600; font-size: 12px; }}
        tr:hover {{ background-color: #f1f5f9; }}
        
        /* リンクボタンのデザイン */
        .tv-btn {{ 
            text-decoration: none; 
            font-size: 12px; 
            font-weight: bold; 
            padding: 4px 8px; 
            border-radius: 4px; 
            display: inline-block;
        }}
        .overview {{ background-color: #2563eb; color: white; }}
        .chart {{ background-color: #f1f5f9; color: #2563eb; border: 1px solid #2563eb; }}
        .overview:hover {{ background-color: #1d4ed8; }}
        .chart:hover {{ background-color: #2563eb; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 米国株 10倍株スクリーナー</h1>
        <p class="update-time">最終更新(UTC): {update_time} | 条件: $50M-$5B / 成長率5%↑ / 価格$1↑</p>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>該当銘柄なし</p>"}
        </div>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Update complete! {len(df)} candidates identified.")
