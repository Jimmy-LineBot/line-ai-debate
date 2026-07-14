import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

GEMINI_BASE = "https://generativelanguage.googleapis.com"
GEMINI_PATH = "/v1beta/models/gemini-2.0-flash:generateContent"

async def call_gemini(prompt, system_prompt=""):
    url = GEMINI_BASE + GEMINI_PATH + "?key=" + GOOGLE_AI_API_KEY
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }
    if system_prompt:
        payload["systemInstruction"] = {
            "parts": [{"text": system_prompt}]
        }
    payload["generationConfig"] = {
        "temperature": 0.8,
        "maxOutputTokens": 1024,
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                print("Gemini status: " + str(response.status_code))
                if response.status_code == 429:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print("Gemini error: " + str(e))
            if attempt < 2:
                await asyncio.sleep(3)
                continue
            return "Gemini unavailable"
    return "Gemini unavailable"

async def call_llama(prompt, system_prompt=""):
    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json",
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                print("Llama status: " + str(response.status_code))
                if response.status_code == 429:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                if response.status_code != 200:
                    print("Llama body: " + response.text[:200])
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print("Llama error: " + str(e))
            if attempt < 2:
                await asyncio.sleep(3)
                continue
            return "Llama unavailable"
    return "Llama unavailable"

async def call_cohere(prompt, system_prompt=""):
    url = "https://api.cohere.com/v1/chat"
    payload = {
        "model": "command-r-plus",
        "message": prompt,
        "temperature": 0.8,
        "max_tokens": 1024,
    }
    if system_prompt:
        payload["preamble"] = system_prompt
    headers = {
        "Authorization": "Bearer " + COHERE_API_KEY,
        "Content-Type": "application/json",
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                print("Cohere status: " + str(response.status_code))
                if response.status_code == 429:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                if response.status_code != 200:
                    print("Cohere body: " + response.text[:200])
                response.raise_for_status()
                data = response.json()
                return data["text"]
        except Exception as e:
            print("Cohere error: " + str(e))
            if attempt < 2:
                await asyncio.sleep(3)
                continue
            return "Cohere unavailable"
    return "Cohere unavailable"
