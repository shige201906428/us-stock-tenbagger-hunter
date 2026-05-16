# Tenbagger Screener Setup Guide

このプロジェクトは、GitHub Actionsを使用して毎日米国株をスクリーニングし、結果を `index.html` としてGitHub Pagesに公開するものです。

## 構成ファイル
1. `screener.py`: 10倍株の判定ロジックとHTML生成
2. `requirements.txt`: 必要なライブラリ
3. `.github/workflows/daily_scan.yml`: 自動実行設定

## 手順
1. GitHubで新しいリポジトリを作成。
2. これらのファイルをアップロード。
3. リポジトリの Settings > Pages で、Sourceを `gh-pages` ブランチに設定。
