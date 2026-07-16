import logging
from ddgs import DDGS

logger = logging.getLogger(__name__)

REMOVE_WORDS = [
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

PUNCT = "?!。，,、
"

def extract_keywords(query):
    """Shorten query for search."""
    short = query
    for r in REMOVE_WORDS:
        short = short.replace(r, " ")
    # Remove punctuation
    for p in PUNCT:
        short = short.replace(p, " ")
    # Collapse spaces
    while "  " in short:
        short = short.replace("  ", " ")
    short = short.strip()
    # Take first few words if too long
    if len(short) > 40:
        parts = short.split(" ")
        short = " ".join(parts[:6])
    return short

async def web_search(query):
    """Search with ddgs metasearch."""
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
                        "Search %s: %d hits",
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

async def check_search_status():
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
