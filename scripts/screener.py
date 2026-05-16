import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures
import random
import time

def get_russell_2000_tickers():
    """WikipediaからRussell 2000のリストを取得"""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        tables = pd.read_html(url)
        df = tables[2] 
        tickers = df['Ticker'].tolist()
        return [str(t).replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"List fetch error: {e}")
        # バックアップ用リスト（取得失敗時）
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]

def process_stock(symbol):
    """個別の銘柄を分析（データ欠損対策済み）"""
    try:
        stock = yf.Ticker(symbol)
        # 1. infoの取得（タイムアウト対策として軽量にアクセス）
        info = stock.info
        if not info: return None

        # --- フィルタリング条件 ---
        
        # 時価総額 $5.0B以下 (上限だけ設定してヒット率を上げる)
        mcap = info.get('marketCap', 0)
        if mcap > 5_000_000_000 or mcap == 0:
            return None

        # 売上成長率の取得 (1.info 2.financials の順で試行)
        growth = info.get('revenueGrowth')
        if growth is None:
            # infoに無い場合は直近2年の財務データから計算
            fin = stock.get_financials(year=2)
            if not fin.empty and 'Total Revenue' in fin.index and len(fin.columns) >= 2:
                rev = fin.loc['Total Revenue']
                if rev.iloc[1] > 0:
                    growth = (rev.iloc[0] / rev.iloc[1]) - 1
        
        # 成長率がプラス(>0)なら合格
        if growth is None or growth <= 0:
            return None

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
# 毎日違う銘柄に出会えるようランダムに1000社抽出
target_tickers = random.sample(all_tickers, min(len(all_tickers), 1000))

print(f"🎲 Random Scan Start: {len(target_tickers)} tickers selected.")

found_stocks = []
# Actionsの負荷を考慮し、並列数は15程度が安定します
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    results = list(executor.map(process_stock, target_tickers))

found_stocks = [r for r in results if r is not None]
df = pd.DataFrame(found_stocks)

# --- TradingView リンク生成 (確実なUSリンク) ---
def make_tv_links(symbol):
    ov_url = f"https://www.tradingview.com/symbols/{symbol}/"
    ct_url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    return (f'<a href="{ov_url}" target="_blank" class="tv-btn detail">Detail</a> '
            f'<a href="{ct_url}" target="_blank" class="tv-btn chart">📈 Chart</a>')

if not df.empty:
    df.insert(0, 'TradingView', df['Symbol'].apply(make_tv_links))

# --- HTML出力 (デザイン微調整) ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Tenbagger Hunter</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; color: #212529; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        h1 {{ color: #0d6efd; font-size: 28px; margin-bottom: 5px; }}
        .meta {{ font-size: 13px; color: #6c757d; margin-bottom: 20px; border-bottom: 1px solid #dee2e6; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #dee2e6; text-align: left; font-size: 14px; }}
        th {{ background: #f8f9fa; color: #495057; font-weight: 600; text-transform: uppercase; }}
        tr:hover {{ background: #f1f3f5; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 4px 10px; border-radius: 6px; font-size: 12px; display: inline-block; transition: 0.2s; }}
        .detail {{ background: #0d6efd; color: white; }}
        .chart {{ border: 1px solid #0d6efd; color: #0d6efd; margin-left: 5px; }}
        .detail:hover {{ background: #0b5ed7; }}
        .chart:hover {{ background: #0d6efd; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 Daily Random Tenbagger Hunter</h1>
        <div class="meta">Last Update: {update_time} (UTC) | Sample: 1,000 stocks from Russell 2000</div>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found in this sample. Try running again!</p>"}
        </div>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Update Complete. {len(found_stocks)} stocks matched.")
