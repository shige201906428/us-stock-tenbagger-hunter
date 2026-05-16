import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import time

def get_russell_2000_tickers():
    """
    WikipediaからRussell 2000のリストを取得する
    """
    try:
        # Russell 2000のリストが掲載されているページ（取得先を安定したURLに設定）
        url = "https://en.wikipedia.org/wiki/List_of_Russell_2000_companies"
        tables = pd.read_html(url)
        # Wikipediaのテーブル構造からティッカー列を特定
        df = tables[2] 
        tickers = df['Ticker'].tolist()
        # 不要な文字（ドットをハイフンに変換など）を処理
        return [t.replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"List fetch error: {e}")
        # 取得失敗時のバックアップ
        return ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY"]

def check_tenbagger_potential(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # --- 10倍株のスクリーニング条件 ---
        
        # 1. 時価総額 ($100M - $2.5B) 
        # Russell 2000の中でも特に「伸び代」がある小型〜中型に限定
        mcap = info.get('marketCap', 0)
        if not (100_000_000 <= mcap <= 2_500_000_000):
            return None

        # 2. 売上高成長率 (25%以上)
        # 若い会社の絶対条件である「売上の急拡大」を確認
        financials = stock.financials
        if 'Total Revenue' in financials.index and len(financials.columns) >= 2:
            rev = financials.loc['Total Revenue']
            growth = (rev.iloc[0] / rev.iloc[1]) - 1
            if growth < 0.25:
                return None
        else:
            return None
            
        # 3. PSR (15倍以下)
        # 割高すぎるものは避け、適正な期待値の銘柄を拾う
        psr = info.get('priceToSalesTrailing12Months', 100)
        if psr > 15: 
            return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Sector": info.get('sector', 'N/A'),
            "Growth": f"{growth:.2%}",
            "PSR": f"{psr:.2f}",
            "MarketCap": f"${mcap/1e6:.1f}M",
            "Price": f"${info.get('currentPrice', 0)}"
        }
    except:
        return None

# --- メイン処理 ---
all_tickers = get_russell_2000_tickers()
# 実行時間を考慮し、まずは最初の500社をスキャン（必要に応じて調整可能）
target_tickers = all_tickers[:500]

found_stocks = []
print(f"Scanning {len(target_tickers)} companies from Russell 2000...")

for i, ticker in enumerate(target_tickers):
    result = check_tenbagger_potential(ticker)
    if result:
        found_stocks.append(result)
        print(f"Match found: {ticker}")
    
    # 連続アクセスによる負荷軽減
    if i % 5 == 0:
        time.sleep(0.2)

df = pd.DataFrame(found_stocks)

# --- HTML生成 ---
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Russell 2000 Tenbagger Hunter</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 30px; background-color: #f0f4f8; }}
        .container {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        h1 {{ color: #2980b9; border-left: 5px solid #2980b9; padding-left: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 25px; }}
        th, td {{ padding: 12px; border: 1px solid #eee; text-align: left; }}
        th {{ background-color: #2980b9; color: white; }}
        tr:hover {{ background-color: #f9f9f9; }}
        .symbol {{ font-weight: bold; color: #d35400; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>米国中小型株 10倍株スクリーナー (Russell 2000対象)</h1>
        <p>更新日時: {update_time} (UTC) | スキャン対象: 上位500社</p>
        {df.to_html(index=False, escape=False) if not df.empty else "<p>条件に合う銘柄は見つかりませんでした。</p>"}
    </div>
</body>
</html>
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Scan completed successfully.")
