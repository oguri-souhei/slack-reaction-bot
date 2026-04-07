#!/usr/bin/env bash
set -e

# .env から環境変数を読み込み
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$NGROK_DOMAIN" ]; then
  echo "ERROR: NGROK_DOMAIN が .env に設定されていません"
  exit 1
fi

# venv が無ければ作成
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

echo "==> uvicorn + ngrok を起動します"
echo "    ngrok domain: $NGROK_DOMAIN"

# uvicorn をバックグラウンドで起動
.venv/bin/uvicorn main:app --reload --port 8000 &
UVICORN_PID=$!

# ngrok を起動
ngrok http --domain="$NGROK_DOMAIN" 8000 &
NGROK_PID=$!

# Ctrl+C で両方を終了
trap "kill $UVICORN_PID $NGROK_PID 2>/dev/null; exit" INT TERM
echo "==> 起動完了 (Ctrl+C で停止)"
wait
