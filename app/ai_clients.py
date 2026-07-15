import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

async def call_mixtral(prompt, system_prompt=""):
    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            print("Mixtral status: " + str(response.status_code))
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("Mixtral error: " + str(e))
        return "Mixtral unavailable"

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
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            print("Llama status: " + str(response.status_code))
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("Llama error: " + str(e))
        return "Llama unavailable"

async def call_cohere(prompt, system_prompt=""):
    url = "https://api.cohere.com/v1/chat"
    payload = {
        "model": "command-a-03-2025",
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
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            print("Cohere status: " + str(response.status_code))
            response.raise_for_status()
            data = response.json()
            return data["text"]
    except Exception as e:
        print("Cohere error: " + str(e))
        return "Cohere unavailable"
