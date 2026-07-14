點 「Add file」 → 「Create new file」
檔名填：app/ai_clients.py
內容貼上：
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

async def call_gemini(prompt: str, system_prompt: str = "") -> str:
    """呼叫 Google Gemini API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_AI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }

    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    payload["generationConfig"] = {
        "temperature": 0.8,
        "maxOutputTokens": 1024,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Gemini 無法回應"

async def call_llama(prompt: str, system_prompt: str = "") -> str:
    """呼叫 Groq (Llama) API"""
    url = "https://api.groq.com/openai/v1/chat/completions"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "Llama 無法回應"

async def call_cohere(prompt: str, system_prompt: str = "") -> str:
    """呼叫 Cohere (Command R+) API"""
    url = "https://api.cohere.com/v2/chat"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "command-r-plus",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        try:
            return data["message"]["content"][0]["text"]
        except (KeyError, IndexError):
            return "Command R+ 無法回應"
