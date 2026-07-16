import httpx
import logging

logger = logging.getLogger(__name__)

DDG_URL = "https://api.duckduckgo.com/"

async def search_web(query: str) -> list:
    """Search using DuckDuckGo."""
    results = []
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    }
    try:
        async with httpx.AsyncClient(
            timeout=10
        ) as client:
            resp = await client.get(
                DDG_URL,
                params=params,
            )
            if resp.status_code != 200:
                logger.error(
                    "DDG error: %s",
                    resp.status_code,
                )
                return []
            data = resp.json()
            # Abstract (top result)
            abstract = data.get("Abstract", "")
            abs_url = data.get("AbstractURL", "")
            abs_src = data.get(
                "AbstractSource", ""
            )
            if abstract:
                results.append(
                    {
                        "title": abs_src,
                        "url": abs_url,
                        "snippet": abstract,
                    }
                )
            # Related topics
            topics = data.get(
                "RelatedTopics", []
            )
            for t in topics[:5]:
                text = t.get("Text", "")
                url = t.get("FirstURL", "")
                if text and url:
                    results.append(
                        {
                            "title": text[:60],
                            "url": url,
                            "snippet": text,
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
    params = {
        "q": "test",
        "format": "json",
        "no_html": "1",
    }
    try:
        async with httpx.AsyncClient(
            timeout=10
        ) as client:
            resp = await client.get(
                DDG_URL,
                params=params,
            )
            return resp.status_code
    except Exception:
        return 500
