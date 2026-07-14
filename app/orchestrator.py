import asyncio
from app.ai_clients import call_gemini
from app.ai_clients import call_llama
from app.ai_clients import call_cohere

NL = chr(10)

async def run_debate(question):
    sys_prompt = "You are an analyst. Reply in Traditional Chinese. Be concise."

    r1_prompt = "Please analyze: " + question

    r1_gemini, r1_llama, r1_cohere = await asyncio.gather(
        call_gemini(r1_prompt, sys_prompt),
        call_llama(r1_prompt, sys_prompt),
        call_cohere(r1_prompt, sys_prompt),
        return_exceptions=True,
    )

    r1_gemini = str(r1_gemini) if isinstance(r1_gemini, Exception) else r1_gemini
    r1_llama = str(r1_llama) if isinstance(r1_llama, Exception) else r1_llama
    r1_cohere = str(r1_cohere) if isinstance(r1_cohere, Exception) else r1_cohere

    r2_base = "Original question: " + question + NL
    r2_gemini_p = r2_base + "Opinion A: " + r1_llama + NL + "Opinion B: " + r1_cohere + NL + "Please rebut or supplement."
    r2_llama_p = r2_base + "Opinion A: " + r1_gemini + NL + "Opinion B: " + r1_cohere + NL + "Please rebut or supplement."
    r2_cohere_p = r2_base + "Opinion A: " + r1_gemini + NL + "Opinion B: " + r1_llama + NL + "Please rebut or supplement."

    r2_gemini, r2_llama, r2_cohere = await asyncio.gather(
        call_gemini(r2_gemini_p, sys_prompt),
        call_llama(r2_llama_p, sys_prompt),
        call_cohere(r2_cohere_p, sys_prompt),
        return_exceptions=True,
    )

    r2_gemini = str(r2_gemini) if isinstance(r2_gemini, Exception) else r2_gemini
    r2_llama = str(r2_llama) if isinstance(r2_llama, Exception) else r2_llama
    r2_cohere = str(r2_cohere) if isinstance(r2_cohere, Exception) else r2_cohere

    r3_prompt = (
        "Question: " + question + NL
        + "Round 1:" + NL
        + "Gemini: " + r1_gemini + NL
        + "Llama: " + r1_llama + NL
        + "Command R+: " + r1_cohere + NL
        + "Round 2:" + NL
        + "Gemini: " + r2_gemini + NL
        + "Llama: " + r2_llama + NL
        + "Command R+: " + r2_cohere + NL
        + "Give final recommendation in Traditional Chinese within 300 chars."
    )

    r3_sys = "You are a final analyst. Reply in Traditional Chinese."
    final = await call_gemini(r3_prompt, r3_sys)

    sep = NL + "=" * 20 + NL
    output = (
        "AI Discussion Result" + sep
        + "Question: " + question + sep
        + "Round 1:" + NL + NL
        + "Gemini:" + NL + r1_gemini + NL + NL
        + "Llama:" + NL + r1_llama + NL + NL
        + "Command R+:" + NL + r1_cohere + sep
        + "Round 2:" + NL + NL
        + "Gemini:" + NL + r2_gemini + NL + NL
        + "Llama:" + NL + r2_llama + NL + NL
        + "Command R+:" + NL + r2_cohere + sep
        + "Final:" + NL + final
    )

    return output
