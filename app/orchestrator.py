import asyncio
from app.ai_clients import call_gemini
from app.ai_clients import call_llama
from app.ai_clients import call_cohere

NL = chr(10)
SEP = NL + "=" * 20 + NL

async def run_debate(question):
    sys1 = "You are an expert analyst. Always reply in Traditional Chinese. Be specific with details."

    r1_prompt = "Please give your analysis and recommendation for this question (within 200 words): " + question

    r1_gemini, r1_llama, r1_cohere = await asyncio.gather(
        call_gemini(r1_prompt, sys1),
        call_llama(r1_prompt, sys1),
        call_cohere(r1_prompt, sys1),
        return_exceptions=True,
    )

    r1_gemini = str(r1_gemini) if isinstance(r1_gemini, Exception) else r1_gemini
    r1_llama = str(r1_llama) if isinstance(r1_llama, Exception) else r1_llama
    r1_cohere = str(r1_cohere) if isinstance(r1_cohere, Exception) else r1_cohere

    await asyncio.sleep(15)

    sys2 = "You are a debate expert. You MUST disagree or find flaws in the other opinions. Reply in Traditional Chinese."

    r2_base = "Original question: " + question + NL + NL

    r2_gemini_p = (
        r2_base
        + "Here are two other AI opinions:" + NL
        + "Opinion A: " + r1_llama + NL + NL
        + "Opinion B: " + r1_cohere + NL + NL
        + "You MUST point out what is WRONG or MISSING in their answers. Disagree with at least one point. Add what they missed."
    )
    r2_llama_p = (
        r2_base
        + "Here are two other AI opinions:" + NL
        + "Opinion A: " + r1_gemini + NL + NL
        + "Opinion B: " + r1_cohere + NL + NL
        + "You MUST point out what is WRONG or MISSING in their answers. Disagree with at least one point. Add what they missed."
    )
    r2_cohere_p = (
        r2_base
        + "Here are two other AI opinions:" + NL
        + "Opinion A: " + r1_gemini + NL + NL
        + "Opinion B: " + r1_llama + NL + NL
        + "You MUST point out what is WRONG or MISSING in their answers. Disagree with at least one point. Add what they missed."
    )

    r2_gemini, r2_llama, r2_cohere = await asyncio.gather(
        call_gemini(r2_gemini_p, sys2),
        call_llama(r2_llama_p, sys2),
        call_cohere(r2_cohere_p, sys2),
        return_exceptions=True,
    )

    r2_gemini = str(r2_gemini) if isinstance(r2_gemini, Exception) else r2_gemini
    r2_llama = str(r2_llama) if isinstance(r2_llama, Exception) else r2_llama
    r2_cohere = str(r2_cohere) if isinstance(r2_cohere, Exception) else r2_cohere

    sys3 = "You are a final judge. Synthesize all opinions into one clear recommendation. Reply in Traditional Chinese."

    r3_prompt = (
        "Question: " + question + NL + NL
        + "=== Round 1 Opinions ===" + NL
        + "Gemini said: " + r1_gemini + NL
        + "Llama said: " + r1_llama + NL
        + "Command R+ said: " + r1_cohere + NL + NL
        + "=== Round 2 Rebuttals ===" + NL
        + "Gemini rebuttal: " + r2_gemini + NL
        + "Llama rebuttal: " + r2_llama + NL
        + "Command R+ rebuttal: " + r2_cohere + NL + NL
        + "Now give the FINAL ANSWER that directly answers the original question. Combine the best parts from all opinions. If the question asks for a plan or list, provide the complete plan or list. Do not just say which opinion is better. Give the actual answer the user needs. Within 500 words."
    )

    final = await call_llama(r3_prompt, sys3)

    output = (
        "AI Discussion Result" + SEP
        + "Question: " + question + SEP
        + "Round 1 - Independent Opinions:" + NL + NL
        + "Gemini:" + NL + r1_gemini + NL + NL
        + "Llama:" + NL + r1_llama + NL + NL
        + "Command R+:" + NL + r1_cohere + SEP
        + "Round 2 - Rebuttals:" + NL + NL
        + "Gemini:" + NL + r2_gemini + NL + NL
        + "Llama:" + NL + r2_llama + NL + NL
        + "Command R+:" + NL + r2_cohere + SEP
        + "FINAL CONCLUSION:" + NL + final
    )

    return output
