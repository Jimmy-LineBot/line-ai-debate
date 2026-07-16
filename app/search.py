import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX", "")

BASE_URL = "https://www.googleapis.com/customsearch/v1"

async def web_search(query, num_results=5):
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_SEARCH_CX,
        "q": query,
        "num": num_results,
        "lr": "lang_zh-TW",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(BASE_URL, params=params)
            print("Search status: " + str(response.status_code))
            if response.status_code != 200:
                print("Search error: " + response.text[:200])
                return ""
            data = response.json()
            items = data.get("items", [])
            results = []
            for item in items:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                results.append(title + ": " + snippet + " (" + link + ")")
            return "
".join(results)
    except Exception as e:
        print("Search exception: " + str(e))
        return ""
