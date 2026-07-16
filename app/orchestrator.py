import asyncio
from app.ai_clients import call_mixtral
from app.ai_clients import call_llama
from app.ai_clients import call_cohere
from app.search import web_search_multi

NL = chr(10)
SEP = NL + "=" * 20 + NL

NO_SEARCH_NOTE = (
    "NOTE: No search results found."
    " You MUST NOT invent any URL."
    " If you cannot find a real website,"
    " say so and suggest search keywords."
    " Do NOT make up store names or links."
)

def make_search_ctx(text):
    """Wrap search results."""
    if text:
        return (
            NL
            + "=== Web Search Results ==="
            + NL + text + NL
            + "=== End Search Results ==="
            + NL
            + "IMPORTANT: Only use URLs from"
            + " the search results above."
            + " Do NOT invent URLs." + NL
        )
    return NL + NO_SEARCH_NOTE + NL

def shorten(text, limit=300):
    """Shorten text to limit chars."""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."

async def run_debate(question):
    search_list = await web_search_multi(
        question, n=3
    )
    ctx_a = make_search_ctx(search_list[0])
    ctx_b = make_search_ctx(search_list[1])
    ctx_c = make_search_ctx(search_list[2])

    sys1 = (
        "You are an expert analyst."
        " Always reply in Traditional Chinese."
        " Be specific with details."
        " Only cite URLs from search results."
        " If no results, say so."
        " NEVER invent or guess URLs."
        " NEVER make up website names."
    )

    r1_prompt_a = (
        "Analyze and recommend"
        " (within 200 words): "
        + question + NL + ctx_a
    )
    r1_prompt_b = (
        "Analyze and recommend"
        " (within 200 words): "
        + question + NL + ctx_b
    )
    r1_prompt_c = (
        "Analyze and recommend"
        " (within 200 words): "
        + question + NL + ctx_c
    )

    # Round 1: Mixtral first, then Llama
    # Cohere in parallel with Llama
    r1_mixtral = await call_mixtral(
        r1_prompt_a, sys1
    )
    await asyncio.sleep(2)
    r1_llama, r1_cohere = await asyncio.gather(
        call_llama(r1_prompt_b, sys1),
        call_cohere(r1_prompt_c, sys1),
    )

    await asyncio.sleep(10)

    sys2 = (
        "You are a debate expert."
        " You MUST disagree or find flaws."
        " Reply in Traditional Chinese."
        " NEVER invent URLs or store names."
        " Be concise (within 200 words)."
    )

    all_ctx = make_search_ctx(
        search_list[0]
    )

    # Shorten Round 1 for Round 2 prompts
    s_mixtral = shorten(r1_mixtral)
    s_llama = shorten(r1_llama)
    s_cohere = shorten(r1_cohere)

    r2_mixtral_p = (
        "Question: " + question + NL
        + all_ctx + NL
        + "Opinion A: " + s_llama + NL + NL
        + "Opinion B: " + s_cohere + NL + NL
        + "Point out what is WRONG."
    )
    r2_llama_p = (
        "Question: " + question + NL
        + all_ctx + NL
        + "Opinion A: " + s_mixtral + NL + NL
        + "Opinion B: " + s_cohere + NL + NL
        + "Point out what is WRONG."
    )
    r2_cohere_p = (
        "Question: " + question + NL
        + all_ctx + NL
        + "Opinion A: " + s_mixtral + NL + NL
        + "Opinion B: " + s_llama + NL + NL
        + "Point out what is WRONG."
    )

    # Round 2: Mixtral first, then Llama
    r2_mixtral = await call_mixtral(
        r2_mixtral_p, sys2
    )
    await asyncio.sleep(2)
    r2_llama, r2_cohere = await asyncio.gather(
        call_llama(r2_llama_p, sys2),
        call_cohere(r2_cohere_p, sys2),
    )

    await asyncio.sleep(10)

    sys3 = (
        "You are a senior debate expert."
        " Review ALL opinions and rebuttals."
        " Find remaining flaws."
        " Reply in Traditional Chinese."
        " NEVER invent URLs."
        " Be brief (within 150 words)."
    )

    # Shorten for Round 3
    s2_mixtral = shorten(r2_mixtral)
    s2_llama = shorten(r2_llama)
    s2_cohere = shorten(r2_cohere)

    r3_all = (
        "Question: " + question + NL
        + all_ctx + NL
        + "Round 1:" + NL
        + "Mixtral: " + s_mixtral + NL
        + "Llama: " + s_llama + NL
        + "Cohere: " + s_cohere + NL + NL
        + "Round 2:" + NL
        + "Mixtral: " + s2_mixtral + NL
        + "Llama: " + s2_llama + NL
        + "Cohere: " + s2_cohere + NL + NL
        + "Give your FINAL rebuttal."
    )

    # Round 3: Mixtral first, then Llama
    r3_mixtral = await call_mixtral(
        r3_all, sys3
    )
    await asyncio.sleep(2)
    r3_llama, r3_cohere = await asyncio.gather(
        call_llama(r3_all, sys3),
        call_cohere(r3_all, sys3),
    )

    await asyncio.sleep(10)

    sys4 = (
        "You are a final judge."
        " Synthesize all opinions into one"
        " clear recommendation."
        " Reply in Traditional Chinese."
        " RULES:"
        " 1. Only include URLs from search."
        " 2. If no verified URL, suggest"
        " keywords for user to Google."
        " 3. NEVER make up URLs."
        " 4. Ignore fake URLs from others."
        " Within 500 words."
    )

    r4_prompt = (
        "Question: " + question + NL
        + all_ctx + NL
        + "Round 1:" + NL
        + "Mixtral: " + s_mixtral + NL
        + "Llama: " + s_llama + NL
        + "Cohere: " + s_cohere + NL + NL
        + "Round 2:" + NL
        + "Mixtral: " + s2_mixtral + NL
        + "Llama: " + s2_llama + NL
        + "Cohere: " + s2_cohere + NL + NL
        + "Round 3:" + NL
        + "Mixtral: " + shorten(r3_mixtral)
        + NL
        + "Llama: " + shorten(r3_llama) + NL
        + "Cohere: " + shorten(r3_cohere)
        + NL + NL
        + "Give the FINAL ANSWER."
    )

    final = await call_llama(r4_prompt, sys4)
    if not final or "unavailable" in final:
        final = await call_mixtral(
            r4_prompt, sys4
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
