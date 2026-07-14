import os
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
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Gemini no response"

async def call_llama(prompt, system_prompt=""):
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
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "Llama no response"

async def call_cohere(prompt, system_prompt=""):
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
        "Authorization": "Bearer " + COHERE_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        try:
            return data["message"]["content"][0]["text"]
        except (KeyError, IndexError):
            return "Cohere no response"
