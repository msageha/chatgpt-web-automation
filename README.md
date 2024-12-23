# ChatGPT Web Automation Client

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[!CAUTION]
**OpenAIの規約違反に当たる可能性があります。**
**自己責任でお願いします。**

## 特徴

- **モデル選択対応**: GPT-4やGPT-3.5など、UI上で提供されるモデルを切り替え可能  
- **画像入力対応**: Vision対応モデルを想定し、画像を入力して解析可能  
- **自動ログイン・リトライ**: Cloudflare対策画面やログイン失敗時のリトライ処理  
- **ログ・デバッグ強化**: ログローテーション、エラー時スクリーンショット、DOMダンプ取得  

## 前提条件

- Python 3.12を推奨
- Google Chromeおよび対応するバージョンの `chromedriver`
- OpenAIアカウント (ChatGPT利用可能なもの)
  - ただし、ログインする場合はアカウントBANされる可能性あるので注意
- OS: Linux / macOS / Windows

## セットアップ

1. リポジトリをクローン:

``` bash
git clone https://github.com/msageha/chatgpt-web-automation
cd chatgpt-web-automation
```

2. 環境変数の設定（任意）:

ログインする場合、環境変数にメールアドレスとパスワードを設定。

``` bash
export CHATGPT_EMAIL=your_email@example.com
export CHATGPT_PASSWORD=your_password
```

3. 環境構築:

``` bash
make setup
source .venv/bin/activate
```

## 使い方

- 基本的な実行:

``` bash
python -m src.main
```

- モデル指定:

``` bash
python -m src.main --model gpt-4
```

- ログレベル変更・ヘッドレス無効化:

``` bash
python -m src.main --log-level DEBUG --headless False
```
