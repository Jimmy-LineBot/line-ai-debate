import logging
from ddgs import DDGS

logger = logging.getLogger(__name__)

async def web_search(query: str) -> str:
    """Search with ddgs metasearch."""
    results = []
    # Try google backend first
    backends = ["google", "brave"]
    for be in backends:
        try:
            with DDGS() as ddgs:
                hits = ddgs.text(
                    query,
                    max_results=5,
                    backend=be,
                )
                if not hits:
                    continue
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
                if results:
                    break
        except Exception as e:
            logger.warning(
                "Search %s failed: %s",
                be, e,
            )
            continue
    if not results:
        logger.warning(
            "No results for: %s",
            query,
        )
        return ""
    text = chr(10).join(results)
    logger.info(
        "Search got %d results (%s): %s",
        len(results),
        backends[0] if results else "none",
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
                backend="google",
            )
            if hits:
                return 200
            return 204
    except Exception:
        return 500
