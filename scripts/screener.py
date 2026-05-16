import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures
import random
import time

def get_russell_2000_tickers():
    """WikipediaからRussell 2000の全リストを取得"""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        # lxmlを使用してHTMLの表を読み込む
        tables = pd.read_html(url)
        df = tables[2] 
        tickers = df['Ticker'].tolist()
        return [str(t).replace('.', '-') for t in tickers if isinstance(t, str)]
    except Exception as e:
        print(f"List fetch error: {e}")
        # 万が一失敗した時の予備
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]

def process_stock(symbol):
    """個別の銘柄を分析"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info: return None

        # フィルター：時価総額 $5.0B以下 (10倍株候補のサイズ)
        mcap = info.get('marketCap', 0)
        if mcap > 5_000_000_000 or mcap == 0:
            return None

        # フィルター：売上成長率がプラス (>0)
        growth = info.get('revenueGrowth')
        if growth is None:
            # infoにない場合のみ財務データをチェック
            fin = stock.get_financials(year=2)
            if not fin.empty and 'Total Revenue' in fin.index:
                rev = fin.loc['Total Revenue']
                if len(rev) >= 2 and rev.iloc[1] > 0:
                    growth = (rev.iloc[0] / rev.iloc[1]) - 1
        
        if growth is None or growth <= 0:
            return None

        # フィルター：株価$1以上
        price = info.get('currentPrice', 0)
        if price < 1.0: return None

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
# 2000社の中から毎日違う1000社をランダム抽出
target_tickers = random.sample(all_tickers, min(len(all_tickers), 1000))

print(f"🚀 High-Speed Scan Start: {len(target_tickers)} tickers selected.")

found_stocks = []
# 10並列でスキャン（GitHub Actionsで最も安定する速度）
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_stock, target_tickers))

found_stocks = [r for r in results if r is not None]
df = pd.DataFrame(found_stocks)

# --- TradingView ダブルリンク生成 ---
def make_tv_links(symbol):
    ov_url = f"https://www.tradingview.com/symbols/{symbol}/"
    ct_url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    return (f'<a href="{ov_url}" target="_blank" class="tv-btn detail">Detail</a> '
            f'<a href="{ct_url}" target="_blank" class="tv-btn chart">📈 Chart</a>')

if not df.empty:
    df.insert(0, 'TradingView', df['Symbol'].apply(make_tv_links))

# --- HTML出力 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Tenbagger Hunter 1000</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; color: #212529; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
        h1 {{ color: #2563eb; font-size: 26px; border-left: 6px solid #2563eb; padding-left: 15px; margin-bottom: 5px; }}
        .meta {{ font-size: 13px; color: #6c757d; margin-bottom: 25px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; font-size: 14px; }}
        th {{ background: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; }}
        tr:hover {{ background: #f1f7ff; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 4px 10px; border-radius: 6px; font-size: 11px; display: inline-block; transition: 0.2s; }}
        .detail {{ background: #2563eb; color: white; }}
        .chart {{ border: 1px solid #2563eb; color: #2563eb; margin-left: 5px; }}
        .detail:hover {{ background: #1d4ed8; }}
        .chart:hover {{ background: #2563eb; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Daily Random Tenbagger Hunter</h1>
        <div class="meta">Last Update: {update_time} (UTC) | Scanned: 1,000 stocks from Russell 2000 | Matches: {len(found_stocks)}</div>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found today. The market might be tough!</p>"}
        </div>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Scan Finished. Matches: {len(found_stocks)}")
