import asyncio
from app.ai_clients import call_mixtral
from app.ai_clients import call_llama
from app.ai_clients import call_cohere
from app.search import web_search

NL = chr(10)
SEP = NL + "=" * 20 + NL

NO_SEARCH_NOTE = (
    "NOTE: No web search results available."
    " You MUST NOT invent or guess any URL."
    " If you do not know a real website,"
    " say you cannot find one."
    " Do NOT make up store names or links."
)

async def run_debate(question):
    search_results = await web_search(question)

    search_context = ""
    if search_results:
        search_context = (
            NL
            + "=== Web Search Results ==="
            + NL
            + search_results + NL
            + "=== End Search Results ==="
            + NL + NL
            + "IMPORTANT: Only use URLs from"
            + " the search results above."
            + " Do NOT invent URLs." + NL
        )
    else:
        search_context = NL + NO_SEARCH_NOTE + NL

    sys1 = (
        "You are an expert analyst."
        " Always reply in Traditional Chinese."
        " Be specific with details."
        " IMPORTANT: Only cite URLs that"
        " appear in the search results."
        " If no search results are provided,"
        " say you cannot find verified info."
        " NEVER invent or guess URLs."
        " NEVER make up website names."
    )

    r1_prompt = (
        "Please give your analysis and"
        " recommendation for this question"
        " (within 200 words): "
        + question + NL + search_context
    )

    r1_mixtral, r1_llama, r1_cohere = (
        await asyncio.gather(
            call_mixtral(r1_prompt, sys1),
            call_llama(r1_prompt, sys1),
            call_cohere(r1_prompt, sys1),
        )
    )

    sys2 = (
        "You are a debate expert."
        " You MUST disagree or find flaws"
        " in the other opinions."
        " Reply in Traditional Chinese."
        " Base your rebuttal on facts and"
        " the search results provided."
        " NEVER invent URLs or store names."
        " If you cannot verify a URL,"
        " point out it may be fake."
    )

    r2_base = (
        "Original question: "
        + question + NL
        + search_context + NL
    )

    r2_mixtral_p = (
        r2_base
        + "Here are two other AI opinions:"
        + NL
        + "Opinion A: " + r1_llama + NL + NL
        + "Opinion B: " + r1_cohere + NL + NL
        + "You MUST point out what is WRONG"
        + " or MISSING in their answers."
        + " If they provide unverified URLs,"
        + " call them out."
        + " Add what they missed."
    )
    r2_llama_p = (
        r2_base
        + "Here are two other AI opinions:"
        + NL
        + "Opinion A: " + r1_mixtral + NL + NL
        + "Opinion B: " + r1_cohere + NL + NL
        + "You MUST point out what is WRONG"
        + " or MISSING in their answers."
        + " If they provide unverified URLs,"
        + " call them out."
        + " Add what they missed."
    )
    r2_cohere_p = (
        r2_base
        + "Here are two other AI opinions:"
        + NL
        + "Opinion A: " + r1_mixtral + NL + NL
        + "Opinion B: " + r1_llama + NL + NL
        + "You MUST point out what is WRONG"
        + " or MISSING in their answers."
        + " If they provide unverified URLs,"
        + " call them out."
        + " Add what they missed."
    )

    r2_mixtral, r2_llama, r2_cohere = (
        await asyncio.gather(
            call_mixtral(r2_mixtral_p, sys2),
            call_llama(r2_llama_p, sys2),
            call_cohere(r2_cohere_p, sys2),
        )
    )

    sys3 = (
        "You are a senior debate expert."
        " Review ALL previous opinions and"
        " rebuttals."
        " Find any remaining flaws or add"
        " final insights."
        " Reply in Traditional Chinese."
        " NEVER invent URLs."
    )

    r3_all = (
        "Original question: "
        + question + NL
        + search_context + NL
        + "=== Round 1 ===" + NL
        + "Mixtral: " + r1_mixtral + NL
        + "Llama: " + r1_llama + NL
        + "Command R+: " + r1_cohere + NL + NL
        + "=== Round 2 Rebuttals ===" + NL
        + "Mixtral: " + r2_mixtral + NL
        + "Llama: " + r2_llama + NL
        + "Command R+: " + r2_cohere + NL + NL
        + "Now give your FINAL rebuttal."
        + " What did everyone still get wrong?"
        + " Be brief (within 150 words)."
    )

    r3_mixtral, r3_llama, r3_cohere = (
        await asyncio.gather(
            call_mixtral(r3_all, sys3),
            call_llama(r3_all, sys3),
            call_cohere(r3_all, sys3),
        )
    )

    sys4 = (
        "You are a final judge."
        " Synthesize all opinions into one"
        " clear recommendation."
        " Reply in Traditional Chinese."
        " CRITICAL RULES:"
        " 1. Only include URLs from search"
        " results."
        " 2. If no verified URL exists,"
        " tell user to search keywords"
        " on Google themselves."
        " 3. NEVER make up website names"
        " or URLs."
        " 4. If other AIs provided fake"
        " URLs, ignore those URLs."
    )

    r4_prompt = (
        "Question: " + question + NL
        + search_context + NL
        + "=== Round 1 Opinions ===" + NL
        + "Mixtral: " + r1_mixtral + NL
        + "Llama: " + r1_llama + NL
        + "Command R+: " + r1_cohere + NL + NL
        + "=== Round 2 Rebuttals ===" + NL
        + "Mixtral: " + r2_mixtral + NL
        + "Llama: " + r2_llama + NL
        + "Command R+: " + r2_cohere + NL + NL
        + "=== Round 3 Final ===" + NL
        + "Mixtral: " + r3_mixtral + NL
        + "Llama: " + r3_llama + NL
        + "Command R+: " + r3_cohere + NL + NL
        + "Now give the FINAL ANSWER."
        + " Only use verified URLs from"
        + " search results."
        + " If no URL was found, tell user"
        + " to search these keywords:"
        + " and suggest good search terms."
        + " Within 500 words."
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
