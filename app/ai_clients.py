import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

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

async def call_mixtral(
    prompt, system_prompt="", max_tok=1024
):
    return await _groq_call(
        "openai/gpt-oss-120b",
        prompt,
        system_prompt,
        max_tok,
    )

async def call_llama(
    prompt, system_prompt="", max_tok=1024
):
    return await _groq_call(
        "llama-3.3-70b-versatile",
        prompt,
        system_prompt,
        max_tok,
    )

async def call_cohere(
    prompt, system_prompt="", max_tok=1024
):
    url = "https://api.cohere.com/v1/chat"
    payload = {
        "model": "command-a-03-2025",
        "message": prompt,
        "temperature": 0.8,
        "max_tokens": max_tok,
    }
    if system_prompt:
        payload["preamble"] = system_prompt
    headers = {
        "Authorization": "Bearer "
        + COHERE_API_KEY,
        "Content-Type": "application/json",
    }
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
            resp.raise_for_status()
            data = resp.json()
            return data["text"]
    except Exception as e:
        print("Cohere error: " + str(e))
        return "Cohere unavailable"
