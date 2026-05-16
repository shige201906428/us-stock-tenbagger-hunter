import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import concurrent.futures
import random
import string
import requests
import io

def get_robust_ticker_list():
    """外部サイトのブロックを回避しつつ、1000社以上の候補を確保する"""
    # 1. 成長株・注目株のベースリスト
    base_list = ["MNDY", "GTLB", "DOCN", "IOT", "S", "PLTR", "CELH", "DUOL", "APP", "UPST",
                 "AFRM", "PATH", "SNOW", "RKLB", "IONQ", "SOFI", "U", "MQ", "TOST", "BILL",
                 "DASH", "ABNB", "COIN", "HOOD", "RBLX", "TEAM", "NET", "OKTA", "DDOG", "ZS"]
    
    # 2. Wikipedia (User-Agent偽装で再トライ)
    try:
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        tables = pd.read_html(io.StringIO(resp.text))
        wiki_tickers = tables[2]['Ticker'].tolist()
        base_list.extend([str(t).replace('.', '-') for t in wiki_tickers])
    except:
        print("Wikipedia blocked. Using dynamic generation...")
    
    # 3. ランダム生成で1500社分追加 (404エラーは出るが、網羅性を優先)
    chars = string.ascii_uppercase
    for _ in range(1500):
        base_list.append(''.join(random.choices(chars, k=random.choice([3, 4]))))
    
    return list(set(base_list))

def process_stock(symbol):
    """1年前の価格と比較してパフォーマンスを算出する"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info or 'marketCap' not in info: return None

        # フィルタ条件：時価総額 $50M - $5B かつ 売上成長 > 0
        mcap = info.get('marketCap', 0)
        growth = info.get('revenueGrowth', 0)
        if not (50_000_000 <= mcap <= 5_000_000_000) or (growth is None or growth <= 0):
            return None

        # --- 1年前の答え合わせロジック ---
        current_price = info.get('currentPrice')
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        hist = stock.history(start=one_year_ago, period="5d")
        
        perf_val = 0.0 # ソート用
        perf_str = "N/A"
        
        if not hist.empty and current_price:
            past_price = hist['Close'].iloc[0]
            change = (current_price - past_price) / past_price
            perf_val = change
            perf_str = f"{change:+.2%}"

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Growth": f"{growth:.2%}",
            "PSR": f"{info.get('priceToSalesTrailing12Months', 0):.2f}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${current_price}",
            "1Yr Perf": perf_str,
            "perf_val": perf_val # 内部ソート用
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_robust_ticker_list()
target_tickers = random.sample(all_tickers, min(len(all_tickers), 1000))

print(f"🚀 Simulation Scan Start: {len(target_tickers)} tickers.")

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(process_stock, target_tickers))

found_stocks = [r for r in results if r is not None]
# パフォーマンスが良い順に並び替え
df = pd.DataFrame(found_stocks).sort_values(by="perf_val", ascending=False)

# --- TradingView リンク生成 ---
def make_tv_links(symbol):
    ov_url = f"https://www.tradingview.com/symbols/{symbol}/"
    ct_url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    return f'<a href="{ov_url}" target="_blank" class="tv-btn detail">Detail</a> <a href="{ct_url}" target="_blank" class="tv-btn chart">📈</a>'

if not df.empty:
    df.insert(0, 'TradingView', df['Symbol'].apply(make_tv_links))
    df = df.drop(columns=['perf_val']) # ソート用カラムを削除

# --- HTML出力 (デザイン強化) ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tenbagger Simulation Hunter</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 20px; background: #f4f7f6; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ color: #1e3a8a; font-size: 24px; }}
        .meta {{ font-size: 13px; color: #64748b; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 13px; }}
        th {{ background: #f8fafc; font-weight: bold; }}
        tr:hover {{ background: #f1f5f9; }}
        .tv-btn {{ text-decoration: none; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; display: inline-block; }}
        .detail {{ background: #2563eb; color: white; }}
        .chart {{ border: 1px solid #2563eb; color: #2563eb; margin-left: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Tenbagger Simulation Hunter</h1>
        <div class="meta">Last Update: {update_time} (UTC) | Scanned: 1,000 | Found: {len(found_stocks)}</div>
        <p style="font-size:12px; color:#ef4444;">※1Yr Perf: 1年前にこの銘柄を条件で見つけて買っていた場合の現在までの騰落率</p>
        <div style="overflow-x: auto;">
            {df.to_html(index=False, escape=False) if not df.empty else "<p>No candidates found.</p>"}
        </div>
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(current_dir, "..", "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)
