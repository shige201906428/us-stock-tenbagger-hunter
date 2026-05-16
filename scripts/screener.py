import yfinance as yf
import pandas as pd
from datetime import datetime
import os

def check_tenbagger_potential(symbol):
    """
    10倍株（テンバガー）の候補をスクリーニングするロジック
    """
    try:
        # データの取得（期間を絞って高速化）
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 1. 時価総額チェック ($100M - $2.5B) 
        # 10倍を狙うには小さすぎず大きすぎない中小型株がターゲット
        market_cap = info.get('marketCap', 0)
        if not (100_000_000 <= market_cap <= 2_500_000_000):
            return None

        # 2. 売上高成長率 (直近年度 vs 前年度)
        # 成長株の絶対条件である25%以上の伸びを確認
        financials = stock.financials
        if 'Total Revenue' in financials.index and len(financials.columns) >= 2:
            rev = financials.loc['Total Revenue']
            growth = (rev.iloc[0] / rev.iloc[1]) - 1
            if growth < 0.25:
                return None
        else:
            return None
            
        # 3. PSR (株価売上高倍率)
        # 期待先行で割高すぎないか（15倍以下）をチェック
        psr = info.get('priceToSalesTrailing12Months', 100)
        if psr > 15: 
            return None

        return {
            "Symbol": symbol,
            "Name": info.get('shortName', 'N/A'),
            "Sector": info.get('sector', 'N/A'),
            "Growth": f"{growth:.2%}",
            "PSR": f"{psr:.2f}",
            "MarketCap": f"${market_cap/1e6:.1f}M",
            "Price": f"${info.get('currentPrice', 0)}"
        }
    except Exception as e:
        print(f"Error checking {symbol}: {e}")
        return None

# --- メイン処理 ---

# 解析対象のティッカーリスト（ここを適宜増やしてください）
# 次世代の成長が期待される銘柄を中心にピックアップ
ticker_list = ["PLTR", "CELH", "DUOL", "S", "IOT", "MNDY", "DOCN", "GTLB", "UPST", "AFRM"]
found_stocks = []

print(f"Starting scan for {len(ticker_list)} tickers...")

for ticker in ticker_list:
    result = check_tenbagger_potential(ticker)
    if result:
        print(f"Found match: {ticker}")
        found_stocks.append(result)

df = pd.DataFrame(found_stocks)

# --- HTML生成 ---

# 日本時間(JST)に合わせた表記
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tenbagger Candidate Screener</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f7f9; color: #333; }}
        .container {{ max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 15px; border: 1px solid #eee; text-align: left; }}
        th {{ background-color: #3498db; color: white; text-transform: uppercase; font-size: 0.9em; }}
        tr:hover {{ background-color: #f1f9ff; }}
        .update-time {{ color: #7f8c8d; font-size: 0.85em; margin-bottom: 20px; }}
        .symbol {{ font-weight: bold; color: #e67e22; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>米国株 10倍株候補スクリーナー</h1>
        <p class="update-time">最終更新日時: {update_time} (UTC)</p>
        {df.to_html(index=False, classes='table', escape=False) if not df.empty else "<p>現在、条件を満たす銘柄はありません。</p>"}
        <p style="margin-top: 30px; font-size: 0.8em; color: #95a5a6;">
            ※条件: 時価総額 $100M-$2.5B / 売上成長率 25%UP / PSR 15以下
        </p>
    </div>
</body>
</html>
"""

# --- 保存処理 ---

# スクリプトが scripts/ にあることを前提に、1つ上のルート階層に index.html を出す
current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "..", "index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully saved results to {index_path}")
