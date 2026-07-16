import logging
from ddgs import DDGS

logger = logging.getLogger(__name__)

async def web_search(query: str) -> str:
    """Search with DuckDuckGo."""
    results = []
    try:
        with DDGS() as ddgs:
            hits = ddgs.text(
                query,
                max_results=5,
                region="tw-tzh",
            )
            for i, h in enumerate(hits, 1):
                title = h.get("title", "")
                url = h.get("href", "")
                body = h.get("body", "")
                if not url:
                    continue
                line = (
                    str(i) + ". "
                    + title + chr(10)
                    + "   " + url + chr(10)
                    + "   " + body
                )
                results.append(line)
    except Exception as e:
        logger.error(
            "Search failed: %s", e
        )
    if not results:
        logger.warning(
            "No results for: %s",
            query,
        )
        return ""
    text = chr(10).join(results)
    logger.info(
        "Search got %d results for: %s",
        len(results),
        query[:50],
    )
    return text

async def check_search_status() -> int:
    """Check if search works."""
    try:
        with DDGS() as ddgs:
            hits = ddgs.text(
                "hello",
                max_results=1,
                region="tw-tzh",
            )
            if hits:
                return 200
            return 204
    except Exception:
        return 500
