import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SEARCH_KEY = os.getenv(
    "GOOGLE_SEARCH_API_KEY", ""
)
SEARCH_CX = os.getenv(
    "GOOGLE_SEARCH_CX", ""
)

BASE = "https://www.googleapis.com"
PATH = "/customsearch/v1"

async def web_search(query, num=5):
    url = BASE + PATH
    params = {
        "key": SEARCH_KEY,
        "cx": SEARCH_CX,
        "q": query,
        "num": num,
        "lr": "lang_zh-TW",
    }
    try:
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            r = await client.get(
                url, params=params
            )
            print(
                "Search status: "
                + str(r.status_code)
            )
            if r.status_code != 200:
                return ""
            data = r.json()
            items = data.get("items", [])
            out = []
            for item in items:
                t = item.get("title", "")
                s = item.get("snippet", "")
                k = item.get("link", "")
                line = t + ": " + s
                out.append(line)
            joined = chr(10).join(out)
            return joined
    except Exception as e:
        print("Search err: " + str(e))
        return ""
