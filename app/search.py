import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

async def web_search(query: str) -> list:
    """Search using duckduckgo-search."""
    results = []
    try:
        with DDGS() as ddgs:
            hits = ddgs.text(
                query,
                max_results=5,
            )
            for h in hits:
                results.append(
                    {
                        "title": h.get(
                            "title", ""
                        ),
                        "url": h.get(
                            "href", ""
                        ),
                        "snippet": h.get(
                            "body", ""
                        ),
                    }
                )
    except Exception as e:
        logger.error(
            "Search failed: %s", e
        )
    return results

async def check_search_status() -> int:
    """Check if search works."""
    try:
        with DDGS() as ddgs:
            hits = ddgs.text(
                "test",
                max_results=1,
            )
            if hits:
                return 200
            return 204
    except Exception:
        return 500
