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

async def run_debate(question):
    # Search 3 different angles
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

    r1_mixtral, r1_llama, r1_cohere = (
        await asyncio.gather(
            call_mixtral(r1_prompt_a, sys1),
            call_llama(r1_prompt_b, sys1),
            call_cohere(r1_prompt_c, sys1),
        )
    )

    # Delay to avoid 429
    await asyncio.sleep(5)

    sys2 = (
        "You are a debate expert."
        " You MUST disagree or find flaws."
        " Reply in Traditional Chinese."
        " NEVER invent URLs or store names."
        " If they cited unverified URLs,"
        " call them out."
    )

    all_ctx = make_search_ctx(
        search_list[0]
    )

    r2_base = (
        "Original question: "
        + question + NL + all_ctx + NL
    )

    r2_mixtral_p = (
        r2_base
        + "Opinion A: " + r1_llama + NL + NL
        + "Opinion B: " + r1_cohere + NL + NL
        + "Point out what is WRONG."
    )
    r2_llama_p = (
        r2_base
        + "Opinion A: " + r1_mixtral + NL + NL
        + "Opinion B: " + r1_cohere + NL + NL
        + "Point out what is WRONG."
    )
    r2_cohere_p = (
        r2_base
        + "Opinion A: " + r1_mixtral + NL + NL
        + "Opinion B: " + r1_llama + NL + NL
        + "Point out what is WRONG."
    )

    r2_mixtral, r2_llama, r2_cohere = (
        await asyncio.gather(
            call_mixtral(r2_mixtral_p, sys2),
            call_llama(r2_llama_p, sys2),
            call_cohere(r2_cohere_p, sys2),
        )
    )

    # Delay to avoid 429
    await asyncio.sleep(5)

    sys3 = (
        "You are a senior debate expert."
        " Review ALL opinions and rebuttals."
        " Find remaining flaws."
        " Reply in Traditional Chinese."
        " NEVER invent URLs."
        " Be brief (within 150 words)."
    )

    r3_all = (
        "Original question: "
        + question + NL + all_ctx + NL
        + "=== Round 1 ===" + NL
        + "Mixtral: " + r1_mixtral + NL
        + "Llama: " + r1_llama + NL
        + "Command R+: " + r1_cohere + NL + NL
        + "=== Round 2 ===" + NL
        + "Mixtral: " + r2_mixtral + NL
        + "Llama: " + r2_llama + NL
        + "Command R+: " + r2_cohere + NL + NL
        + "Give your FINAL rebuttal."
    )

    r3_mixtral, r3_llama, r3_cohere = (
        await asyncio.gather(
            call_mixtral(r3_all, sys3),
            call_llama(r3_all, sys3),
            call_cohere(r3_all, sys3),
        )
    )

    # Delay before final
    await asyncio.sleep(3)

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
        + "=== Round 1 ===" + NL
        + "Mixtral: " + r1_mixtral + NL
        + "Llama: " + r1_llama + NL
        + "Command R+: " + r1_cohere + NL + NL
        + "=== Round 2 ===" + NL
        + "Mixtral: " + r2_mixtral + NL
        + "Llama: " + r2_llama + NL
        + "Command R+: " + r2_cohere + NL + NL
        + "=== Round 3 ===" + NL
        + "Mixtral: " + r3_mixtral + NL
        + "Llama: " + r3_llama + NL
        + "Command R+: " + r3_cohere + NL + NL
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
