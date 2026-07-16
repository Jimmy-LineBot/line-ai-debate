import httpx
import logging
import re

logger = logging.getLogger(__name__)

DDG_HTML = "https://html.duckduckgo.com/html/"

async def web_search(query: str) -> list:
    """Search using DuckDuckGo HTML."""
    results = []
    data = {
        "q": query,
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0"
            " (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36"
        ),
    }
    try:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
        ) as client:
            resp = await client.post(
                DDG_HTML,
                data=data,
                headers=headers,
            )
            if resp.status_code != 200:
                logger.error(
                    "DDG status: %s",
                    resp.status_code,
                )
                return []
            html = resp.text
            # Parse results from HTML
            blocks = re.findall(
                r'class="result__a"'
                r'.*?href="(.*?)"'
                r'.*?>(.*?)</a>'
                r'.*?class="result__snippet'
                r'".*?>(.*?)</',
                html,
                re.DOTALL,
            )
            for url, title, snippet in blocks:
                if not url or not title:
                    continue
                # Clean HTML tags
                title = re.sub(
                    r"<.*?>", "", title
                )
                snippet = re.sub(
                    r"<.*?>", "", snippet
                )
                # Decode URL
                if "/l/?uddg=" in url:
                    from urllib.parse import (
                        unquote,
                    )
                    parts = url.split(
                        "uddg="
                    )
                    if len(parts) > 1:
                        url = unquote(
                            parts[1].split(
                                "&"
                            )[0]
                        )
                results.append(
                    {
                        "title": title.strip(),
                        "url": url,
                        "snippet": snippet.strip(),
                    }
                )
                if len(results) >= 5:
                    break
    except Exception as e:
        logger.error(
            "Search failed: %s", e
        )
    return results

async def check_search_status() -> int:
    """Check if DuckDuckGo works."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0"
            " (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36"
        ),
    }
    try:
        async with httpx.AsyncClient(
            timeout=10,
            follow_redirects=True,
        ) as client:
            resp = await client.post(
                DDG_HTML,
                data={"q": "test"},
                headers=headers,
            )
            return resp.status_code
    except Exception:
        return 500
