# Slack 自動スタンプ Bot

感謝・了承を表すメッセージに自動でリアクション（絵文字スタンプ）を付与する Slack Bot。

## 機能

- 「ありがとう」「thanks」などの感謝ワードを検出してリアクションを付与
- リアクションはランダムに選択（:pray: :thumbsup: :clap: :muscle: :raised_hands:）
- 対象ユーザーへのメンション or 対象ユーザーが参加しているスレッドのみ反応
- 対象ユーザー自身の投稿には反応しない

## セットアップ

### 1. 依存ライブラリのインストール

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集して以下を設定:

| 変数名 | 説明 | 例 |
|---|---|---|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token | `xoxb-xxxxxxxxxxxx` |
| `TARGET_USER_ID` | リアクション対象のユーザー ID | `U0XXXXXXXXX` |
| `NGROK_DOMAIN` | ngrok の Static Domain | `your-name-here.ngrok-free.app` |

### 3. Slack App の設定

1. [https://api.slack.com/apps](https://api.slack.com/apps) で新規 App を作成
2. **Bot Token Scopes** に以下を追加:
   - `reactions:write` — スタンプの付与
   - `channels:history` — パブリックチャンネルのメッセージ受信
   - `im:history` — DM のメッセージ受信
   - `groups:history` — プライベートチャンネルのメッセージ受信（任意）
3. **Event Subscriptions** を有効化:
   - Request URL: `https://<your-domain>.ngrok-free.app/slack/events`
   - Subscribe to bot events: `message.channels`, `message.im`, `message.groups`（任意）
4. ワークスペースにインストールし、Bot Token を `.env` に設定
5. 動作確認したいチャンネルで `/invite @<Bot名>` を実行

## 起動

```bash
./start.sh
```

uvicorn と ngrok が同時に起動します。`Ctrl+C` で両方停止します。
