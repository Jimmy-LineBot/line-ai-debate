import os
import logging
import httpx

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SERP_URL = "https://serpapi.com/search"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

async def ai_extract_queries(question):
    """Use AI to generate 2 search queries."""
    url = (
        "https://api.groq.com"
        "/openai/v1/chat/completions"
    )
    sys_msg = (
        "You extract search keywords."
        " Given a question, output 2 lines."
        " Line1: ALL important nouns and"
        " topic words from the question"
        " plus the word 'recommend' in the"
        " same language. Max 8 words."
        " Line2: Only the MAIN subject"
        " (1-2 words) plus 'recommend'."
        " RULES:"
        " - Remove filler words like"
        " please, I want, can you, etc."
        " - Keep product names, locations,"
        " categories."
        " - Always end with recommend word."
        " - Same language as question."
        " - Do NOT include 'PTT' in output."
        " Example question: recommend"
        " traditional iron for kids"
        " school uniform on PTT"
        " Example output:"
        " traditional iron kids uniform"
        " recommend"
        " iron recommend"
    )
    messages = [
        {"role": "system",
         "content": sys_msg},
        {"role": "user",
         "content": question},
    ]
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 80,
    }
    headers = {
        "Authorization": "Bearer "
        + GROQ_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(
            timeout=10
        ) as client:
            resp = await client.post(
                url,
                json=payload,
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                text = (
                    data["choices"][0]
                    ["message"]["content"]
                ).strip()
                lines = text.split(chr(10))
                detailed = lines[0].strip()
                detailed = detailed.replace(
                    "Line1:", ""
                ).replace(
                    "Line 1:", ""
                ).strip()
                broad = ""
                if len(lines) >= 2:
                    broad = lines[1].strip()
                    broad = broad.replace(
                        "Line2:", ""
                    ).replace(
                        "Line 2:", ""
                    ).strip()
                logger.info(
                    "AI queries: [%s] [%s]",
                    detailed, broad,
                )
                return detailed, broad
    except Exception as e:
        logger.warning(
            "AI extract failed: %s", e
        )
    return None, None

def fallback_keywords(query):
    """Fallback: simple keyword extract."""
    removes = [
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
        chr(30452) + chr(25509) + chr(32102)
        + chr(25105),
        chr(30475) + chr(26377) + chr(27794)
        + chr(26377),
        chr(26377) + chr(27794) + chr(26377),
        chr(21738) + chr(20491) + chr(32178)
        + chr(31449),
        chr(35201) + chr(21435) + chr(21738)
        + chr(20491) + chr(32178) + chr(31449)
        + chr(36023),
        chr(32178) + chr(31449),
        chr(30452) + chr(25509) + chr(32102)
        + chr(25105) + chr(32178) + chr(22336),
        chr(20320) + chr(20497) + chr(25512)
        + chr(34214),
        chr(25512) + chr(34214) + chr(30340),
    ]
    puncts = [
        "?", "!", chr(12290), chr(65292),
        ",", chr(12289), chr(10),
        chr(65311), chr(65281),
    ]
    short = query
    for r in removes:
        short = short.replace(r, " ")
    for p in puncts:
        short = short.replace(p, " ")
    while "  " in short:
        short = short.replace("  ", " ")
    short = short.strip()
    if len(short) > 50:
        parts = short.split(" ")
        short = " ".join(parts[:7])
    return short

def _add_ptt(q, question):
    """Add PTT keyword if mentioned."""
    if "PTT" in question or "ptt" in question:
        if "PTT" not in q and "ptt" not in q:
            q = q + " PTT"
    return q

async def _serpapi_search(query, num=10):
    """Call SerpAPI Google search."""
    if not SERPAPI_KEY:
        logger.error("No SERPAPI_KEY set")
        return []
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "engine": "google",
        "num": num,
        "hl": "zh-TW",
        "gl": "tw",
    }
    results = []
    try:
        async with httpx.AsyncClient(
            timeout=15
        ) as client:
            resp = await client.get(
                SERP_URL, params=params,
            )
            if resp.status_code != 200:
                logger.error(
                    "SerpAPI status: %s",
                    resp.status_code,
                )
                return []
            data = resp.json()
            organic = data.get(
                "organic_results", []
            )
            for i, item in enumerate(
                organic, 1
            ):
                title = item.get("title", "")
                url = item.get("link", "")
                snippet = item.get(
                    "snippet", ""
                )
                if not url:
                    continue
                results.append({
                    "i": i,
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "content": "",
                })
    except Exception as e:
        logger.error(
            "SerpAPI error: %s", e
        )
    return results

async def _fetch_page(url):
    """Fetch page text content (first 1500 chars)."""
    try:
        async with httpx.AsyncClient(
            timeout=8,
            follow_redirects=True,
        ) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0"
                        " (Windows NT 10.0)"
                        " AppleWebKit/537.36"
                    ),
                },
            )
            if resp.status_code != 200:
                return ""
            html = resp.text
            # Simple HTML to text
            import re
            # Remove scripts and styles
            html = re.sub(
                r"<script.*?</script>",
                "", html, flags=re.DOTALL
            )
            html = re.sub(
                r"<style.*?</style>",
                "", html, flags=re.DOTALL
            )
            # Remove tags
            text = re.sub(
                r"<[^>]+>", " ", html
            )
            # Collapse whitespace
            text = re.sub(
                r"\s+", " ", text
            ).strip()
            # Return first 1500 chars
            return text[:1500]
    except Exception:
        return ""

async def _enrich_results(results, top_n=3):
    """Fetch page content for top N results."""
    for item in results[:top_n]:
        content = await _fetch_page(
            item["url"]
        )
        if content:
            item["content"] = content
    return results

def _format_results(results):
    """Format results as text."""
    lines = []
    for item in results:
        line = (
            str(item["i"]) + ". "
            + item["title"] + chr(10)
            + "   " + item["url"] + chr(10)
            + "   " + item["snippet"]
        )
        if item["content"]:
            # Add first 500 chars of content
            short_content = item["content"]
            if len(short_content) > 500:
                short_content = (
                    short_content[:500] + "..."
                )
            line = line + chr(10) + (
                "   [Content]: "
                + short_content
            )
        lines.append(line)
    return chr(10).join(lines)

async def _search_progressive(question):
    """Search: detailed first, broad if needed."""
    detailed, broad = (
        await ai_extract_queries(question)
    )
    if not detailed:
        detailed = fallback_keywords(question)
    if not broad:
        broad = detailed
    q1 = _add_ptt(detailed, question)
    logger.info("Search detailed: %s", q1)
    results = await _serpapi_search(q1, num=10)
    if len(results) < 3:
        q2 = _add_ptt(broad, question)
        if q2 != q1:
            logger.info(
                "Search broad: %s", q2
            )
            more = await _serpapi_search(
                q2, num=10
            )
            seen = set()
            for r in results:
                seen.add(r["url"])
            for r in more:
                if r["url"] not in seen:
                    results.append(r)
                    seen.add(r["url"])
    # Fetch page content for top 3
    if results:
        results = await _enrich_results(
            results, top_n=3
        )
    return results

async def web_search(query):
    """Search with SerpAPI."""
    results = await _search_progressive(query)
    if not results:
        logger.warning("No results")
        return ""
    logger.info(
        "Search total: %d results",
        len(results),
    )
    return _format_results(results)

async def web_search_split(query):
    """Search, give all results to each AI."""
    results = await _search_progressive(query)
    if not results:
        logger.warning("No results")
        return ["", "", ""]
    all_text = _format_results(results)
    logger.info(
        "Search total: %d results",
        len(results),
    )
    return [all_text, all_text, all_text]

async def check_search_status():
    """Check if SerpAPI works."""
    if not SERPAPI_KEY:
        return 401
    try:
        async with httpx.AsyncClient(
            timeout=10
        ) as client:
            resp = await client.get(
                SERP_URL,
                params={
                    "q": "test",
                    "api_key": SERPAPI_KEY,
                    "engine": "google",
                    "num": 1,
                },
            )
            return resp.status_code
    except Exception:
        return 500
