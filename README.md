# ChatGPT Web Automation Client

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

このリポジトリは、Selenium を使用して ChatGPT の Web インターフェースと自動で対話するための、実運用を見据えたサンプル実装を提供します。  
モデル選択（GPT-4、GPT-3.5等）や画像入力（Vision対応モデルを想定）などの追加機能も盛り込み、包括的なボイラープレートとして機能します。

## 特徴

- **モデル選択対応**: GPT-4やGPT-3.5など、UI上で提供されるモデルを切り替え可能  
- **画像入力対応**: Vision対応モデルを想定し、画像を入力して解析可能  
- **自動ログイン・リトライ**: Cloudflare対策画面やログイン失敗時のリトライ処理  
- **ログ・デバッグ強化**: ログローテーション、エラー時スクリーンショット、DOMダンプ取得  
- **設定管理**: `.env`ファイルやコマンドライン引数による柔軟な設定変更  
- **高品質なコード**: 型アノテーション、Docstring、エラーハンドリング、カスタム例外、lint対応済み

## 前提条件

- Python 3.9以上を推奨
- Google Chromeおよび対応するバージョンの `chromedriver`
- OpenAIアカウント (ChatGPT利用可能なもの)
- OS: Linux / macOS / Windows  
  ※ CI環境としてはGitHub Actionsなどが想定可能

## セットアップ

1. リポジトリをクローン:

``` bash
git clone https://github.com/yourname/chatgpt-web-automation.git
cd chatgpt-web-automation
```

2. 環境変数の設定:

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
