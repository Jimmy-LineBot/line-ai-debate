import asyncio
from app.ai_clients import call_mixtral
from app.ai_clients import call_llama
from app.ai_clients import call_cohere
from app.search import web_search_split

NL = chr(10)
SEP = NL + "=" * 20 + NL

NO_SEARCH = (
    "NOTE: No search results found."
    " You MUST NOT invent any URL."
    " Say you cannot find verified info"
    " and suggest search keywords."
)

def wrap_ctx(text):
    """Wrap search results."""
    if text:
        return (
            NL + "=== Search Results ===" + NL
            + text + NL
            + "=== End Results ===" + NL
            + "Only use URLs above."
            + " Do NOT invent URLs." + NL
        )
    return NL + NO_SEARCH + NL

def shorten(text, limit=250):
    """Shorten text to limit chars."""
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."

async def run_debate(question):
    parts = await web_search_split(question)
    ctx_a = wrap_ctx(parts[0])
    ctx_b = wrap_ctx(parts[1])
    ctx_c = wrap_ctx(parts[2])
    all_ctx = wrap_ctx(parts[0])

    sys1 = (
        "You are an expert analyst."
        " Reply in Traditional Chinese."
        " Based on the search results,"
        " give a clear recommendation with:"
        " 1. Your top pick and WHY"
        " 2. Pros and cons"
        " 3. Who it is best for"
        " Only cite URLs from search results."
        " NEVER invent URLs or product names."
        " If the user mentions they already"
        " own something, do NOT recommend"
        " it again."
        " Within 200 words."
    )

    p_a = question + NL + ctx_a
    p_b = question + NL + ctx_b
    p_c = question + NL + ctx_c

    r1_mixtral = await call_mixtral(p_a, sys1)
    await asyncio.sleep(3)
    r1_llama = await call_llama(p_b, sys1)
    r1_cohere = await call_cohere(p_c, sys1)

    await asyncio.sleep(20)

    sys2 = (
        "You are a critical reviewer."
        " Reply in Traditional Chinese."
        " Review the two opinions below."
        " For each opinion:"
        " - If you AGREE, say why and add"
        "   extra info they missed."
        " - If you DISAGREE, explain why"
        "   with evidence from search results."
        " - Point out any WRONG info"
        "   (fake URLs, wrong prices, etc)."
        " - If they recommended something"
        "   the user already owns, call it out."
        " Be constructive, not just negative."
        " Within 200 words."
    )

    sm = shorten(r1_mixtral)
    sl = shorten(r1_llama)
    sc = shorten(r1_cohere)

    r2p_m = (
        question + NL + all_ctx + NL
        + "Opinion A: " + sl + NL
        + "Opinion B: " + sc + NL
        + "Review these opinions."
    )
    r2p_l = (
        question + NL + all_ctx + NL
        + "Opinion A: " + sm + NL
        + "Opinion B: " + sc + NL
        + "Review these opinions."
    )
    r2p_c = (
        question + NL + all_ctx + NL
        + "Opinion A: " + sm + NL
        + "Opinion B: " + sl + NL
        + "Review these opinions."
    )

    r2_mixtral = await call_mixtral(
        r2p_m, sys2
    )
    await asyncio.sleep(3)
    r2_llama = await call_llama(r2p_l, sys2)
    r2_cohere = await call_cohere(r2p_c, sys2)

    await asyncio.sleep(20)

    sys3 = (
        "Senior expert. Review all previous"
        " opinions. Reply in Traditional"
        " Chinese."
        " Identify: 1) What everyone agrees"
        " on 2) Remaining disagreements"
        " 3) Any missing info."
        " NEVER invent URLs."
        " Within 100 words."
    )

    r3p = (
        question + NL + all_ctx + NL
        + "R1: " + sm + " | "
        + sl + " | " + sc + NL
        + "R2: " + shorten(r2_mixtral) + " | "
        + shorten(r2_llama) + " | "
        + shorten(r2_cohere) + NL
        + "Summarize agreements and gaps."
    )

    r3_mixtral = await call_mixtral(r3p, sys3)
    await asyncio.sleep(3)
    r3_llama = await call_llama(r3p, sys3)
    r3_cohere = await call_cohere(r3p, sys3)

    await asyncio.sleep(20)

    sys4 = (
        "Final judge. Give the user a clear,"
        " actionable answer."
        " Reply in Traditional Chinese."
        " Format:"
        " 1. Your #1 recommendation + reason"
        " 2. Runner-up options"
        " 3. Key things to watch out for"
        " Only use verified URLs."
        " If no URL found, suggest search"
        " keywords."
        " NEVER make up URLs or names."
        " Do NOT recommend anything the user"
        " already owns."
        " Within 400 words."
    )

    r4p = (
        "Q: " + question + NL + all_ctx + NL
        + "R1: " + sm + " | "
        + sl + " | " + sc + NL
        + "R2: " + shorten(r2_mixtral) + " | "
        + shorten(r2_llama) + " | "
        + shorten(r2_cohere) + NL
        + "R3: " + shorten(r3_mixtral) + " | "
        + shorten(r3_llama) + " | "
        + shorten(r3_cohere) + NL
        + "Give FINAL ANSWER."
    )

    final = await call_llama(
        r4p, sys4, max_tok=1500
    )
    if not final or "unavailable" in final:
        final = await call_mixtral(
            r4p, sys4, max_tok=1500
        )

    output = (
        "AI Discussion Result" + SEP
        + "Question: " + question + SEP
        + "Round 1:" + NL + NL
        + "Mixtral:" + NL + r1_mixtral
        + NL + NL
        + "Llama:" + NL + r1_llama
        + NL + NL
        + "Command R+:" + NL + r1_cohere + SEP
        + "Round 2:" + NL + NL
        + "Mixtral:" + NL + r2_mixtral
        + NL + NL
        + "Llama:" + NL + r2_llama
        + NL + NL
        + "Command R+:" + NL + r2_cohere + SEP
        + "Round 3:" + NL + NL
        + "Mixtral:" + NL + r3_mixtral
        + NL + NL
        + "Llama:" + NL + r3_llama
        + NL + NL
        + "Command R+:" + NL + r3_cohere + SEP
        + "FINAL CONCLUSION:" + NL + final
    )

    return output
