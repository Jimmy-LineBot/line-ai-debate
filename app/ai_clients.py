import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

DDG_STATUS_URL = (
    "https://duckduckgo.com/duckchat"
    "/v1/status"
)
DDG_CHAT_URL = (
    "https://duckduckgo.com/duckchat"
    "/v1/chat"
)
DDG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0)"
        " AppleWebKit/537.36"
    ),
    "Accept": "text/event-stream",
    "Content-Type": "application/json",
    "Origin": "https://duckduckgo.com",
    "Referer": "https://duckduckgo.com/",
    "x-vqd-accept": "1",
}

NL = chr(10)
NL2 = chr(10) + chr(10)

async def _groq_call(
    model, prompt, system_prompt, max_tok
):
    """Call Groq API with retry on 429."""
    url = (
        "https://api.groq.com"
        "/openai/v1/chat/completions"
    )
    messages = []
    if system_prompt:
        messages.append(
            {"role": "system",
             "content": system_prompt}
        )
    messages.append(
        {"role": "user", "content": prompt}
    )
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": max_tok,
    }
    headers = {
        "Authorization": "Bearer "
        + GROQ_API_KEY,
        "Content-Type": "application/json",
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(
                timeout=60.0
            ) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
                print(
                    model + " status: "
                    + str(resp.status_code)
                )
                if resp.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(
                        model + " 429, wait "
                        + str(wait) + "s"
                    )
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return (
                    data["choices"][0]
                    ["message"]["content"]
                )
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(3)
            else:
                print(
                    model + " error: "
                    + str(e)
                )
    return model + " unavailable"

async def _ddg_chat(prompt, system_prompt):
    """Call DuckDuckGo AI Chat (Claude)."""
    full_prompt = ""
    if system_prompt:
        full_prompt = (
            system_prompt + NL2 + prompt
        )
    else:
        full_prompt = prompt
    try:
        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:
            # Get VQD token
            status_resp = await client.get(
                DDG_STATUS_URL,
                headers=DDG_HEADERS,
            )
            vqd = status_resp.headers.get(
                "x-vqd-4", ""
            )
            if not vqd:
                print("DDG: no vqd token")
                return "DuckDuckGo unavailable"
            # Send chat request
            chat_headers = {
                "User-Agent": (
                    "Mozilla/5.0"
                    " (Windows NT 10.0)"
                    " AppleWebKit/537.36"
                ),
                "Accept": "text/event-stream",
                "Content-Type":
                    "application/json",
                "Origin":
                    "https://duckduckgo.com",
                "Referer":
                    "https://duckduckgo.com/",
                "x-vqd-4": vqd,
            }
            payload = {
                "model": (
                    "claude-3-haiku-20240307"
                ),
                "messages": [
                    {"role": "user",
                     "content": full_prompt}
                ],
            }
            resp = await client.post(
                DDG_CHAT_URL,
                json=payload,
                headers=chat_headers,
            )
            print(
                "DDG Claude status: "
                + str(resp.status_code)
            )
            if resp.status_code != 200:
                return "DuckDuckGo unavailable"
            # Parse SSE response
            result = ""
            for line in resp.text.split(NL):
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        import json
                        obj = json.loads(chunk)
                        msg = obj.get(
                            "message", ""
                        )
                        if msg:
                            result = (
                                result + msg
                            )
                    except Exception:
                        pass
            if result:
                return result
            return "DuckDuckGo unavailable"
    except Exception as e:
        print("DDG error: " + str(e))
        return "DuckDuckGo unavailable"

async def call_mixtral(
    prompt, system_prompt="", max_tok=1500
):
    return await _groq_call(
        "openai/gpt-oss-120b",
        prompt,
        system_prompt,
        max_tok,
    )

async def call_llama(
    prompt, system_prompt="", max_tok=1500
):
    return await _ddg_chat(
        prompt, system_prompt
    )

async def call_cohere(
    prompt, system_prompt="", max_tok=1500
):
    """Call Cohere with retry."""
    url = "https://api.cohere.com/v2/chat"
    payload = {
        "model": "command-a-plus",
        "messages": [
            {"role": "user",
             "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": max_tok,
    }
    if system_prompt:
        payload["messages"].insert(
            0,
            {"role": "system",
             "content": system_prompt}
        )
    headers = {
        "Authorization": "Bearer "
        + COHERE_API_KEY,
        "Content-Type": "application/json",
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(
                timeout=60.0
            ) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
                print(
                    "Cohere status: "
                    + str(resp.status_code)
                )
                if resp.status_code >= 500:
                    wait = 5 * (attempt + 1)
                    print(
                        "Cohere "
                        + str(resp.status_code)
                        + ", wait "
                        + str(wait) + "s"
                    )
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                msg = data.get("message", {})
                content = msg.get(
                    "content", [{}]
                )
                if content:
                    return content[0].get(
                        "text", ""
                    )
                return ""
        except Exception as e:
            if attempt < 2:
                print(
                    "Cohere retry: "
                    + str(e)
                )
                await asyncio.sleep(5)
            else:
                print(
                    "Cohere error: "
                    + str(e)
                )
    return "Cohere unavailable"
