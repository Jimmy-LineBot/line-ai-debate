import logging
from ddgs import DDGS

logger = logging.getLogger(__name__)

REMOVE_WORDS = [
    chr(35531) + chr(25512) + chr(34214),
    chr(35531) + chr(21839),
    chr(25512) + chr(34214),
    chr(25105) + chr(38656) + chr(35201),
    chr(25105) + chr(24819) + chr(35201),
    chr(25105) + chr(35201),
    chr(21487) + chr(20197),
    chr(26368) + chr(22909) + chr(26159),
    chr(26368) + chr(22909),
    chr(35201) + chr(26377),
    chr(30452) + chr(25509) + chr(32102) + chr(25105),
    chr(30475) + chr(26377) + chr(27794) + chr(26377),
    chr(26377) + chr(27794) + chr(26377),
    chr(21738) + chr(20491) + chr(32178) + chr(31449),
    chr(35201) + chr(21435) + chr(21738) + chr(20491)
    + chr(32178) + chr(31449) + chr(36023),
    chr(32178) + chr(31449),
    chr(30452) + chr(25509) + chr(32102)
    + chr(25105) + chr(32178) + chr(22336),
    chr(20320) + chr(20497) + chr(25512)
    + chr(34214),
    chr(25512) + chr(34214) + chr(30340),
]

PUNCT_CHARS = [
    "?", "!", chr(12290), chr(65292),
    ",", chr(12289), chr(10), chr(65311),
    chr(65281),
]

def extract_keywords(query):
    """Shorten query for search."""
    short = query
    for r in REMOVE_WORDS:
        short = short.replace(r, " ")
    for p in PUNCT_CHARS:
        short = short.replace(p, " ")
    while "  " in short:
        short = short.replace("  ", " ")
    short = short.strip()
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
