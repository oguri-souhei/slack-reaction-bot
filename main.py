import os
import re
import random
import logging

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
TARGET_USER_ID = os.environ["TARGET_USER_ID"]

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

REACTIONS = ["pray", "thumbsup", "clap", "muscle", "raised_hands"]

pattern = re.compile("|".join(PATTERNS), re.IGNORECASE)

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

slack_client = httpx.AsyncClient(
    base_url="https://slack.com/api",
    headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
)


async def is_user_in_thread(channel: str, thread_ts: str) -> bool:
    """TARGET_USER_ID がスレッドに参加しているか確認する。"""
    resp = await slack_client.get(
        "/conversations.replies",
        params={"channel": channel, "ts": thread_ts},
    )
    data = resp.json()
    if not data.get("ok"):
        logger.warning(f"⚠️ conversations.replies 失敗: {data}")
        return False
    return any(msg.get("user") == TARGET_USER_ID for msg in data.get("messages", []))


@app.post("/slack/events")
async def slack_events(request: Request):
    body = await request.json()

    # URL Verification
    if body.get("type") == "url_verification":
        return {"challenge": body["challenge"]}

    event = body.get("event", {})

    # Bot メッセージ・編集・削除を除外
    if event.get("bot_id") or event.get("subtype"):
        return {}

    # 対象ユーザー自身の投稿は除外
    if event.get("user") == TARGET_USER_ID:
        return {}

    text = event.get("text", "")
    if not pattern.search(text):
        return {}

    # 対象ユーザーへのメンション判定
    is_mention = f"<@{TARGET_USER_ID}>" in text

    # スレッド内で対象ユーザーが参加しているか判定
    thread_ts = event.get("thread_ts")
    in_thread = False
    if thread_ts:
        in_thread = await is_user_in_thread(event["channel"], thread_ts)

    if not is_mention and not in_thread:
        return {}

    emoji = random.choice(REACTIONS)
    resp = await slack_client.post(
        "/reactions.add",
        json={
            "channel": event["channel"],
            "timestamp": event["ts"],
            "name": emoji,
        },
    )
    result = resp.json()
    if result.get("ok"):
        logger.info(f"✅ :{emoji}: を付与 → {result}")
    else:
        logger.warning(f"⚠️ リアクション付与失敗: {result}")

    return {}
