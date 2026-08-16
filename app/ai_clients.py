import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
COHERE_API_KEY = os.getenv(
    "COHERE_API_KEY", ""
)
MISTRAL_API_KEY = os.getenv(
    "MISTRAL_API_KEY", ""
)

NL = chr(10)
NL2 = chr(10) + chr(10)

async def call_mixtral(
    prompt, system_prompt="", max_tok=1500
):
    """AI 1: GPT-OSS-120B via Groq."""
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
        "model": "openai/gpt-oss-120b",
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
                    "GPT-OSS-120B status: "
                    + str(resp.status_code)
                )
                if resp.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(
                        "GPT-OSS 429, wait "
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
                    "GPT-OSS error: "
                    + str(e)
                )
    return "GPT-OSS-120B unavailable"

async def call_llama(
    prompt, system_prompt="", max_tok=1500
):
    """AI 2: Mistral Large via Mistral API."""
    url = (
        "https://api.mistral.ai"
        "/v1/chat/completions"
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
        "model": "mistral-large-latest",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": max_tok,
    }
    headers = {
        "Authorization": "Bearer "
        + MISTRAL_API_KEY,
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
                    "Mistral Large status: "
                    + str(resp.status_code)
                )
                if resp.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(
                        "Mistral 429, wait "
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
                    "Mistral error: "
                    + str(e)
                )
    return "Mistral Large unavailable"

async def call_cohere(
    prompt, system_prompt="", max_tok=1500
):
    """AI 3: Cohere Command A+."""
    url = "https://api.cohere.com/v2/chat"
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
        "model": "command-a-plus-05-2026",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": max_tok,
    }
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
                if resp.status_code == 422:
                    print(
                        "Cohere 422: "
                        + resp.text[:200]
                    )
                    return (
                        "Cohere model error"
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
