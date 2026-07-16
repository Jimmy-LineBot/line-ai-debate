import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

async def web_search(query: str) -> str:
    """Search with DuckDuckGo."""
    results = []
    try:
        with DDGS() as ddgs:
            hits = ddgs.text(
                query,
                max_results=5,
                region="wt-wt",
            )
            for i, h in enumerate(hits, 1):
                title = h.get("title", "")
                url = h.get("href", "")
                body = h.get("body", "")
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
            "No results for: %s", query
        )
        return ""
    text = chr(10).join(results)
    logger.info(
        "Search got %d results", len(results)
    )
    return text

async def check_search_status() -> int:
    """Check if search works."""
    try:
        with DDGS() as ddgs:
            hits = ddgs.text(
                "test",
                max_results=1,
                region="wt-wt",
            )
            if hits:
                return 200
            return 204
    except Exception:
        return 500
