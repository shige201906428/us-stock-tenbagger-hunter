import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import concurrent.futures
import random
import string

def get_market_tickers():
    """外部サイトに頼らず、主要なティッカーとランダム生成を組み合わせて1000社確保する"""
    # 1. 確実に存在する「成長株・中小型株」のベースリスト
    base_list = [
        "MNDY", "GTLB", "DOCN", "IOT", "S", "PLTR", "CELH", "DUOL", "APP", "UPST",
        "AFRM", "PATH", "SNOW", "RKLB", "IONQ", "SOFI", "U", "MQ", "TOST", "BILL",
        "ALB", "RUN", "ENPH", "SEDG", "CHPT", "BE", "QS", "LCID", "RIVN", "DKNG",
        "DASH", "ABNB", "COIN", "HOOD", "RBLX", "TEAM", "NET", "OKTA", "DDOG", "ZS"
    ]
    
    # 2. 成長株が多いNASDAQのティッカーパターンをランダム生成して「生きた銘柄」を探す
    # (外部のHTMLパースが失敗しても、yfinanceのAPIが生きていればこれでデータが取れる)
    print("Generating dynamic ticker list to bypass blocks...")
    chars = string.ascii_uppercase
    random_extra = []
    while len(random_extra) < 1500:
        length = random.choice([3, 4])
        t = ''.join(random.choices(chars, k=length))
        if t not in base_list:
            random_extra.append(t)
            
    return base_list + random_extra

def process_stock(symbol):
    try:
        # 存在確認も兼ねてfast_infoを使用
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 存在しないティッカーやデータが空のものは即除外
        if not info or 'marketCap' not in info: return None

        mcap = info.get('marketCap', 0)
        # 10バガー条件：時価総額 $50M - $5B
        if not (50_000_000 <= mcap <= 5_000_000_000): return None

        growth = info.get('revenueGrowth', 0)
        # 成長率がプラスの銘柄のみ
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
all_possible = get_market_tickers()
# 2000以上の候補から1000個を試行
target_tickers = random.sample(all_possible, 1000)

print(f"🚀 Global Market Scan Start: {len(target_tickers)} tickers.")

found_stocks = []
# 並列実行（yfinanceのAPI自体がブロックされていなければ、これで数百件ヒットする）
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
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

# --- HTML出力 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dynamic Market Hunter</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f3f4f6; }}
        .container {{ background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 11px; display: inline-block; }}
        .detail {{ background: #1d4ed8; color: white; }}
        .chart {{ border: 1px solid #1d4ed8; color: #1d4ed8; margin-left: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Dynamic Tenbagger Hunter 1000</h1>
        <p>Last Update: {update_time} (UTC) | Scanned: 1,000 | Found: {len(found_stocks)}</p>
        <p style="font-size:12px; color:gray;">*Wikipediaがブロックされたため、動的生成リストでスキャンしています。</p>
        {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found.</p>"}
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(current_dir, "..", "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Update Complete. Found: {len(found_stocks)}")
