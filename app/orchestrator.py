import asyncio
from app.ai_clients import call_mixtral
from app.ai_clients import call_llama
from app.ai_clients import call_cohere

NL = chr(10)
SEP = NL + "=" * 20 + NL

async def run_debate(question):
    sys1 = "You are an expert analyst. Always reply in Traditional Chinese. Be specific with details."

    r1_prompt = "Please give your analysis and recommendation for this question (within 200 words): " + question

    r1_mixtral, r1_llama, r1_cohere = await asyncio.gather(
        call_mixtral(r1_prompt, sys1),
        call_llama(r1_prompt, sys1),
        call_cohere(r1_prompt, sys1),
    )

    sys2 = "You are a debate expert. You MUST disagree or find flaws in the other opinions. Reply in Traditional Chinese."

    r2_base = "Original question: " + question + NL + NL

    r2_mixtral_p = (
        r2_base
        + "Here are two other AI opinions:" + NL
        + "Opinion A: " + r1_llama + NL + NL
        + "Opinion B: " + r1_cohere + NL + NL
        + "You MUST point out what is WRONG or MISSING in their answers. Disagree with at least one point. Add what they missed."
    )
    r2_llama_p = (
        r2_base
        + "Here are two other AI opinions:" + NL
        + "Opinion A: " + r1_mixtral + NL + NL
        + "Opinion B: " + r1_cohere + NL + NL
        + "You MUST point out what is WRONG or MISSING in their answers. Disagree with at least one point. Add what they missed."
    )
    r2_cohere_p = (
        r2_base
        + "Here are two other AI opinions:" + NL
        + "Opinion A: " + r1_mixtral + NL + NL
        + "Opinion B: " + r1_llama + NL + NL
        + "You MUST point out what is WRONG or MISSING in their answers. Disagree with at least one point. Add what they missed."
    )

    r2_mixtral, r2_llama, r2_cohere = await asyncio.gather(
        call_mixtral(r2_mixtral_p, sys2),
        call_llama(r2_llama_p, sys2),
        call_cohere(r2_cohere_p, sys2),
    )

    sys3 = "You are a senior debate expert. Review ALL previous opinions and rebuttals. Find any remaining flaws or add final insights. Reply in Traditional Chinese."

    r3_all = (
        "Original question: " + question + NL + NL
        + "=== Round 1 ===" + NL
        + "Mixtral: " + r1_mixtral + NL
        + "Llama: " + r1_llama + NL
        + "Command R+: " + r1_cohere + NL + NL
        + "=== Round 2 Rebuttals ===" + NL
        + "Mixtral: " + r2_mixtral + NL
        + "Llama: " + r2_llama + NL
        + "Command R+: " + r2_cohere + NL + NL
        + "Now give your FINAL rebuttal. What did everyone still get wrong? What key point is still missing? Be brief (within 150 words)."
    )

    r3_mixtral, r3_llama, r3_cohere = await asyncio.gather(
        call_mixtral(r3_all, sys3),
        call_llama(r3_all, sys3),
        call_cohere(r3_all, sys3),
    )

    sys4 = "You are a final judge. Synthesize all opinions into one clear recommendation. Reply in Traditional Chinese."

    r4_prompt = (
        "Question: " + question + NL + NL
        + "=== Round 1 Opinions ===" + NL
        + "Mixtral: " + r1_mixtral + NL
        + "Llama: " + r1_llama + NL
        + "Command R+: " + r1_cohere + NL + NL
        + "=== Round 2 Rebuttals ===" + NL
        + "Mixtral: " + r2_mixtral + NL
        + "Llama: " + r2_llama + NL
        + "Command R+: " + r2_cohere + NL + NL
        + "=== Round 3 Final Rebuttals ===" + NL
        + "Mixtral: " + r3_mixtral + NL
        + "Llama: " + r3_llama + NL
        + "Command R+: " + r3_cohere + NL + NL
        + "Now give the FINAL ANSWER that directly answers the original question. Combine the best parts from all opinions across all 3 rounds. If the question asks for a plan or list, provide the complete plan or list. Do not just say which opinion is better. Give the actual answer the user needs. Within 500 words."
    )

    final = await call_llama(r4_prompt, sys4)

    output = (
        "AI Discussion Result" + SEP
        + "Question: " + question + SEP
        + "Round 1 - Independent Opinions:" + NL + NL
        + "Mixtral:" + NL + r1_mixtral + NL + NL
        + "Llama:" + NL + r1_llama + NL + NL
        + "Command R+:" + NL + r1_cohere + SEP
        + "Round 2 - Rebuttals:" + NL + NL
        + "Mixtral:" + NL + r2_mixtral + NL + NL
        + "Llama:" + NL + r2_llama + NL + NL
        + "Command R+:" + NL + r2_cohere + SEP
        + "Round 3 - Final Rebuttals:" + NL + NL
        + "Mixtral:" + NL + r3_mixtral + NL + NL
        + "Llama:" + NL + r3_llama + NL + NL
        + "Command R+:" + NL + r3_cohere + SEP
        + "FINAL CONCLUSION:" + NL + final
    )

    return output
