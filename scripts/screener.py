import yfinance as yf
import pandas as pd
from datetime import datetime

def check_tenbagger_potential(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 1. 時価総額チェック ($100M - $2B)
        market_cap = info.get('marketCap', 0)
        if not (100_000_000 <= market_cap <= 2_000_000_000):
            return None

        # 2. 売上高成長率 (直近)
        financials = stock.financials
        if 'Total Revenue' in financials.index and len(financials.columns) >= 2:
            rev = financials.loc['Total Revenue']
            growth = (rev.iloc[0] / rev.iloc[1]) - 1
            if growth < 0.25:
                return None
        else:
            return None
            
        # 3. PSR (株価売上高倍率)
        psr = info.get('priceToSalesTrailing12Months', 100)
        if psr > 15: 
            return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Growth": f"{growth:.2%}",
            "PSR": f"{psr:.2f}",
            "MarketCap": f"${market_cap/1e6:.1f}M",
            "Price": f"${info.get('currentPrice', 0)}"
        }
    except:
        return None

# 解析対象のティッカーリスト
ticker_list = ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB"]
found_stocks = []

for ticker in ticker_list:
    result = check_tenbagger_potential(ticker)
    if result:
        found_stocks.append(result)

df = pd.DataFrame(found_stocks)

# HTML生成 (index.htmlとして書き出し)
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Tenbagger Candidate List</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f0f2f5; }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th, td {{ padding: 15px; border: 1px solid #ddd; text-align: left; }}
        th {{ background-color: #1a73e8; color: white; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .update-time {{ color: #5f6368; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>米国株 10倍株候補スクリーナー</h1>
    <p class="update-time">最終更新日時 (JST): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    {df.to_html(index=False) if not df.empty else "<p>現在、条件に合致する銘柄はありません。</p>"}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
