import yfinance as yf
import pandas as pd
import os

# 1. 調査したい銘柄リスト（自由に変更してください）
tickers = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN"]

results = []

print("スクリーニング開始...")

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        # 直近1ヶ月のデータを取得
        df = stock.history(period="1mo")
        
        if len(df) < 20:
            continue
            
        latest_price = df['Close'].iloc[-1]
        ma20 = df['Close'].mean() # 20日平均
        
        # 条件：現在の株価が20日移動平均より高いか
        is_bullish = latest_price > ma20
        
        results.append({
            "Ticker": ticker,
            "Price": round(latest_price, 2),
            "MA20": round(ma20, 2),
            "Status": "Bullish" if is_bullish else "Bearish"
        })
        print(f"{ticker}: 取得成功")
    except Exception as e:
        print(f"{ticker}: エラー発生 - {e}")

# 2. 結果をCSVに保存
result_df = pd.DataFrame(results)
result_df.to_csv("screening_results.csv", index=False)

print("スクリーニング完了。結果を保存しました。")
