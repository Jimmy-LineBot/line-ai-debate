import os
import asyncio
from fastapi import FastAPI
from fastapi import Request
from fastapi import HTTPException
from linebot.v3 import WebhookParser
from linebot.v3.messaging import AsyncApiClient
from linebot.v3.messaging import AsyncMessagingApi
from linebot.v3.messaging import Configuration
from linebot.v3.messaging import ReplyMessageRequest
from linebot.v3.messaging import PushMessageRequest
from linebot.v3.messaging import TextMessage
from linebot.v3.webhooks import MessageEvent
from linebot.v3.webhooks import TextMessageContent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

channel_secret = os.getenv(
    "LINE_CHANNEL_SECRET", ""
)
channel_access_token = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN", ""
)

configuration = Configuration(
    access_token=channel_access_token
)
parser = WebhookParser(channel_secret)

@app.get("/")
async def root():
    return {"status": "running"}

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get(
        "X-Line-Signature", ""
    )
    body = (await request.body()).decode("utf-8")

    try:
        events = parser.parse(body, signature)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=str(e)
        )

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(
            event.message, TextMessageContent
        ):
            continue

        user_text = event.message.text.strip()
        is_q = user_text.endswith("?")
        is_q = is_q or user_text.endswith("\uff1f")
        is_q = is_q or user_text.startswith("/ask")

        if not is_q:
            continue

        if user_text.startswith("/ask"):
            question = user_text[4:].strip()
        else:
            question = user_text

        part1 = "收到："
        part2 = "

AI討論中請稍候..."
        reply_text = part1 + question + part2

        async with AsyncApiClient(
            configuration
        ) as api_client:
            mapi = AsyncMessagingApi(api_client)
            await mapi.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=reply_text)
                    ],
                )
            )

        source_id = None
        if hasattr(event.source, "group_id"):
            source_id = event.source.group_id
        elif hasattr(event.source, "user_id"):
            source_id = event.source.user_id

        if source_id:
            asyncio.create_task(
                do_debate(source_id, question)
            )

    return "OK"

async def do_debate(source_id, question):
    from app.orchestrator import run_debate

    try:
        result = await run_debate(question)
        async with AsyncApiClient(
            configuration
        ) as api_client:
            mapi = AsyncMessagingApi(api_client)
            msgs = split_msg(result)
            for m in msgs:
                await mapi.push_message(
                    PushMessageRequest(
                        to=source_id,
                        messages=[
                            TextMessage(text=m)
                        ],
                    )
                )
                await asyncio.sleep(0.5)
    except Exception as e:
        err = "Error: " + str(e)
        async with AsyncApiClient(
            configuration
        ) as api_client:
            mapi = AsyncMessagingApi(api_client)
            await mapi.push_message(
                PushMessageRequest(
                    to=source_id,
                    messages=[
                        TextMessage(text=err)
                    ],
                )
            )

def split_msg(text, mx=4500):
    if len(text) <= mx:
        return [text]
    out = []
    while text:
        if len(text) <= mx:
            out.append(text)
            break
        sp = text.rfind("
", 0, mx)
        if sp == -1:
            sp = mx
        out.append(text[:sp])
        text = text[sp:].lstrip("
")
    return out

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, host="0.0.0.0", port=port
    )
