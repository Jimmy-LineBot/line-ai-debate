import logging
import re
from ddgs import DDGS

logger = logging.getLogger(__name__)

def extract_keywords(query: str) -> str:
    """Shorten query for search."""
    # Remove common filler words
    removes = [
        "請推薦", "請問", "推薦",
        "我需要", "我想要", "我要",
        "可以", "最好是", "最好",
        "要有", "直接給我",
        "看有沒有", "有沒有",
        "的是你們推薦的第一名",
        "要去哪個網站買",
        "哪個網站", "網站",
        "直接給我網址",
        "你們推薦", "推薦的",
    ]
    short = query
    for r in removes:
        short = short.replace(r, " ")
    # Remove punctuation
    short = re.sub(
        r"[?？!！。，,、
]+", " ", short
    )
    # Collapse spaces
    short = re.sub(r"\s+", " ", short).strip()
    # Take first 30 chars if still long
    if len(short) > 40:
        words = short.split(" ")
        short = " ".join(words[:6])
    return short

async def web_search(query: str) -> str:
    """Search with ddgs metasearch."""
    # Shorten query for better results
    short_q = extract_keywords(query)
    logger.info("Search query: %s", short_q)

    results = []
    backends = ["google", "brave"]
    for be in backends:
        try:
            with DDGS() as ddgs:
                hits = ddgs.text(
                    short_q,
                    max_results=5,
                    backend=be,
                )
                if not hits:
                    logger.warning(
                        "Search %s: empty", be
                    )
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
                    logger.info(
                        "Search %s got %d",
                        be, len(results),
                    )
                    break
        except Exception as e:
            logger.warning(
                "Search %s failed: %s",
                be, e,
            )
            continue
    if not results:
        logger.warning(
            "No results for: %s", short_q
        )
        return ""
    return chr(10).join(results)

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
