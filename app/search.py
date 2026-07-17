import os
import logging
import random
import httpx

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SERP_URL = "https://serpapi.com/search"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

async def ai_extract_query(question):
    """Use AI to generate search query."""
    url = (
        "https://api.groq.com"
        "/openai/v1/chat/completions"
    )
    sys_msg = (
        "You are a search query generator."
        " Given a user question,"
        " output ONLY a short Google search"
        " query (max 10 words) that would"
        " find the most relevant results."
        " No explanation. Just the query."
        " Output in the same language as"
        " the question."
    )
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": question},
    ]
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 50,
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
                q = (
                    data["choices"][0]
                    ["message"]["content"]
                ).strip().strip('"')
                logger.info(
                    "AI query: %s", q
                )
                return q
    except Exception as e:
        logger.warning(
            "AI extract failed: %s", e
        )
    return None

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

async def _serpapi_search(query, num=30):
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
                line = (
                    str(i) + ". "
                    + title + chr(10)
                    + "   " + url + chr(10)
                    + "   " + snippet
                )
                results.append(line)
    except Exception as e:
        logger.error(
            "SerpAPI error: %s", e
        )
    return results

async def web_search(query):
    """Search with SerpAPI."""
    q = await ai_extract_query(query)
    if not q:
        q = fallback_keywords(query)
    logger.info("Final search: %s", q)
    results = await _serpapi_search(q)
    if not results:
        logger.warning("No results for: %s", q)
        return ""
    logger.info(
        "Search got %d results", len(results)
    )
    return chr(10).join(results)

async def web_search_split(query):
    """Search 30 results, random split."""
    q = await ai_extract_query(query)
    if not q:
        q = fallback_keywords(query)
    logger.info("Final search: %s", q)
    results = await _serpapi_search(q, num=30)
    if not results:
        logger.warning("No results for: %s", q)
        return ["", "", ""]
    shuffled = results[:]
    random.shuffle(shuffled)
    size = len(shuffled) // 3
    group_a = shuffled[:size]
    group_b = shuffled[size:size * 2]
    group_c = shuffled[size * 2:]
    # Re-number each group
    a_lines = []
    for i, line in enumerate(group_a, 1):
        parts = line.split(chr(10), 1)
        if len(parts) == 2:
            idx = parts[0].find(". ")
            new_line = (
                str(i) + parts[0][idx:]
                + chr(10) + parts[1]
            )
            a_lines.append(new_line)
        else:
            a_lines.append(line)
    b_lines = []
    for i, line in enumerate(group_b, 1):
        parts = line.split(chr(10), 1)
        if len(parts) == 2:
            idx = parts[0].find(". ")
            new_line = (
                str(i) + parts[0][idx:]
                + chr(10) + parts[1]
            )
            b_lines.append(new_line)
        else:
            b_lines.append(line)
    c_lines = []
    for i, line in enumerate(group_c, 1):
        parts = line.split(chr(10), 1)
        if len(parts) == 2:
            idx = parts[0].find(". ")
            new_line = (
                str(i) + parts[0][idx:]
                + chr(10) + parts[1]
            )
            c_lines.append(new_line)
        else:
            c_lines.append(line)
    a = chr(10).join(a_lines)
    b = chr(10).join(b_lines)
    c = chr(10).join(c_lines)
    logger.info(
        "Split %d: %d/%d/%d",
        len(results),
        len(group_a),
        len(group_b),
        len(group_c),
    )
    return [a, b, c]

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
