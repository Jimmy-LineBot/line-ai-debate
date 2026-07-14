import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# LINE Bot 設定
channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

configuration = Configuration(access_token=channel_access_token)
parser = WebhookParser(channel_secret)

@app.get("/")
async def root():
    return {"status": "LINE AI Debate Bot is running!"}

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")

    try:
        events = parser.parse(body, signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(
            event.message, TextMessageContent
        ):
            user_text = event.message.text.strip()

            # 判斷是否為提問（問號結尾或 /ask 開頭）
            if user_text.endswith("？") or user_text.endswith("?") or user_text.startswith("/ask"):
                # 移除 /ask 前綴
                question = user_text.replace("/ask", "").strip() if user_text.startswith("/ask") else user_text

                # 先回覆用戶讓他們知道開始處理
                async with AsyncApiClient(configuration) as api_client:
                    messaging_api = AsyncMessagingApi(api_client)
                    await messaging_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[
                                TextMessage(text=f"🤔 收到問題：「{question}」

⏳ 3 個 AI 正在進行討論，請稍候約 15-30 秒...")
                            ],
                        )
                    )

                # 在背景執行辯論
                source_id = None
                if hasattr(event.source, "group_id"):
                    source_id = event.source.group_id
                elif hasattr(event.source, "user_id"):
                    source_id = event.source.user_id

                if source_id:
                    asyncio.create_task(
                        run_debate_and_reply(source_id, question)
                    )

    return "OK"

async def run_debate_and_reply(source_id: str, question: str):
    """背景執行辯論並推送結果"""
    from app.orchestrator import run_debate

    try:
        result = await run_debate(question)

        async with AsyncApiClient(configuration) as api_client:
            messaging_api = AsyncMessagingApi(api_client)

            # 分段發送（LINE 訊息有 5000 字元限制）
            messages = split_message(result)
            for msg in messages:
                await messaging_api.push_message(
                    PushMessageRequest(
                        to=source_id,
                        messages=[TextMessage(text=msg)],
                    )
                )
                await asyncio.sleep(0.5)  # 避免速率限制

    except Exception as e:
        async with AsyncApiClient(configuration) as api_client:
            messaging_api = AsyncMessagingApi(api_client)
            await messaging_api.push_message(
                PushMessageRequest(
                    to=source_id,
                    messages=[TextMessage(text=f"✗ 發生錯誤：{str(e)}
請稍後再試。")],
                )
            )

def split_message(text: str, max_length: int = 4500) -> list:
    """將長文本分割為多個訊息"""
    if len(text) <= max_length:
        return [text]

    messages = []
    while text:
        if len(text) <= max_length:
            messages.append(text)
            break
        # 找到最近的換行符分割
        split_point = text.rfind("
", 0, max_length)
        if split_point == -1:
            split_point = max_length
        messages.append(text[:split_point])
        text = text[split_point:].lstrip("
")

    return messages

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
