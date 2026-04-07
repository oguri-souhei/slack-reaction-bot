# Slack 自動スタンプ Bot 設計書

## 概要

Slack 上で感謝・了承を表すメッセージ（「ありがとうございます」など）が投稿された際に、自動でリアクション（スタンプ）を付与する Bot。

---

## アーキテクチャ

```
User (Slack) → Slack サーバー → ngrok → FastAPI (localhost:8000) → Slack API (reactions.add)
```

1. ユーザーが感謝メッセージを送信
2. Slack が ngrok の公開 URL に Webhook でイベントを POST
3. ngrok がローカルの FastAPI サーバー (port 8000) に転送
4. FastAPI がパターンマッチで感謝ワードを検出
5. Slack の `reactions.add` API を呼び出してスタンプを付与
6. 各層に 200 OK を返す

---

## ディレクトリ構成

```
slack-auto-reaction/
├── .env                  # 環境変数（Gitignore 対象）
├── .gitignore
├── main.py               # FastAPI アプリ本体
├── requirements.txt
└── README.md
```

---

## 環境変数 (.env)

| 変数名            | 説明                 | 例                  |
| ----------------- | -------------------- | ------------------- |
| `SLACK_BOT_TOKEN` | Bot User OAuth Token | `xoxb-xxxxxxxxxxxx` |

---

## 依存ライブラリ (requirements.txt)

```
fastapi
uvicorn[standard]
httpx
python-dotenv
```

---

## 実装仕様

### main.py

#### 感謝ワードパターン

以下の正規表現にマッチするメッセージをトリガーとする。

```python
PATTERNS = [
    r"ありがとう",
    r"ありがと",
    r"助かり",
    r"参考になり",
    r"解決しました",
    r"わかりました",
    r"thanks",
    r"thx",
    r"thank you",
]
```

#### リアクション候補

以下からランダムに 1 つ選択して付与する。

```python
REACTIONS = ["pray", "thumbsup", "clap", "muscle", "raised_hands"]
```

#### エンドポイント: `POST /slack/events`

**処理フロー:**

1. リクエストボディを JSON としてパース
2. `type == "url_verification"` の場合、`challenge` をそのまま返す（Slack App 設定時の初回検証）
3. `event.bot_id` または `event.subtype` が存在する場合は無視して `{}` を返す（Bot メッセージ・編集・削除を除外）
4. `event.text` に対してパターンマッチ
5. マッチした場合、`REACTIONS` からランダムに選択し `reactions.add` を呼び出す
6. 常に `{}` または `{"challenge": ...}` を返す

**Slack `reactions.add` API 呼び出し:**

- URL: `https://slack.com/api/reactions.add`
- Method: POST
- Headers: `Authorization: Bearer {SLACK_BOT_TOKEN}`
- Body:
  ```json
  {
    "channel": "<event.channel>",
    "timestamp": "<event.ts>",
    "name": "<selected_emoji>"
  }
  ```

---

## Slack App 設定手順

### 1. App 作成

[https://api.slack.com/apps](https://api.slack.com/apps) にアクセスし、新規 App を作成（"From scratch"）。

### 2. OAuth Scopes の設定

`OAuth & Permissions` → `Bot Token Scopes` に以下を追加:

| Scope              | 用途                                           |
| ------------------ | ---------------------------------------------- |
| `reactions:write`  | スタンプの付与                                 |
| `channels:history` | パブリックチャンネルのメッセージ受信           |
| `im:history`       | DM のメッセージ受信                            |
| `groups:history`   | プライベートチャンネルのメッセージ受信（任意） |

### 3. Event Subscriptions の設定

`Event Subscriptions` を有効化し、以下を設定:

- **Request URL**: `https://<ngrok_static_domain>/slack/events`
- **Subscribe to bot events**:
  - `message.channels`
  - `message.im`
  - `message.groups`（任意）

### 4. ワークスペースへのインストール

`Install App` からワークスペースにインストールし、`Bot User OAuth Token`（`xoxb-...`）を取得して `.env` に設定。

### 5. Bot をチャンネルに招待

動作確認したいチャンネルで `/invite @<Bot名>` を実行。

---

## ngrok 設定

### Static Domain の取得

ngrok の無料プランで Static Domain が 1 つ利用可能。

```bash
ngrok config add-authtoken <YOUR_NGROK_TOKEN>
```

ダッシュボード（[https://dashboard.ngrok.com](https://dashboard.ngrok.com)）で Static Domain を確認・取得。

### 起動コマンド

```bash
ngrok http --domain=<YOUR_STATIC_DOMAIN>.ngrok-free.app 8000
```

---

## 起動手順

### セットアップ（初回のみ）

```bash
git clone <repository>
cd slack-auto-reaction
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # SLACK_BOT_TOKEN を記入
```

### 起動（ターミナル 2 つ）

```bash
# ターミナル1: FastAPI サーバー
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# ターミナル2: ngrok トンネル
ngrok http --domain=<YOUR_STATIC_DOMAIN>.ngrok-free.app 8000
```

---

## 動作確認

1. 上記の起動手順に従ってサーバーと ngrok を起動
2. Bot を招待済みのチャンネルで「ありがとうございます」と送信
3. メッセージにスタンプが自動付与されることを確認
4. サーバーログに `✅ :pray: を付与 → {'ok': True}` が出力されることを確認

---

## 除外ケース（無視するメッセージ）

- `event.bot_id` が存在する → Bot 自身のメッセージ
- `event.subtype` が存在する → メッセージの編集・削除・参加通知など

---

## エラーハンドリング方針

- `reactions.add` のレスポンスはログに出力する
- `ok: false` の場合もアプリはクラッシュさせず、ログに記録して続行する
- Slack の URL Verification（初回）は `challenge` をそのまま返す

---

## .gitignore

```
.env
.venv/
__pycache__/
*.pyc
```
