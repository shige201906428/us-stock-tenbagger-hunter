import yfinance as yf
import pandas as pd
import datetime

# 1. 調査したい銘柄リスト
tickers = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META"]

results = []

print("スクリーニング開始...")

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        # 直近のデータを取得
        df = stock.history(period="5d")
        
        if df.empty:
            continue
            
        latest_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change = ((latest_price - prev_price) / prev_price) * 100
        
        results.append({
            "銘柄": ticker,
            "現在値": f"${latest_price:.2f}",
            "前日比": f"{change:+.2f}%",
            "更新日時": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        print(f"{ticker}: 取得成功")
    except Exception as e:
        print(f"{ticker}: エラー - {e}")

# 2. データフレーム作成
df_results = pd.DataFrame(results)

# 3. HTMLファイルの生成 (index.html)
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>米国株スクリーニング結果</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body {{ padding: 20px; background-color: #f8f9fa; }}
        .container {{ background: white; padding: 30px; border-radius: 10px; shadow: 0 0 10px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">米国株自動スクリーニング</h1>
        <p>最終更新: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (JST)</p>
        {df_results.to_html(index=False, classes='table table-hover table-bordered')}
    </div>
</body>
</html>
"""

# ファイル保存
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# CSVも保存
df_results.to_csv("screening_results.csv", index=False)

print("すべての処理が完了しました。")
