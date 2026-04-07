import os
import re
import random
import logging

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

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

    text = event.get("text", "")
    if pattern.search(text):
        emoji = random.choice(REACTIONS)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://slack.com/api/reactions.add",
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
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
