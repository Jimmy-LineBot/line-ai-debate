import asyncio
from app.ai_clients import call_gemini, call_llama, call_cohere

async def run_debate(question: str) -> str:
    """
    執行三輪 AI 辯論：
    Round 1: 各 AI 獨立回答
    Round 2: 互相看到對方觀點，進行反駁/補充
    Round 3: 綜合所有討論產出最終建議
    """

    system_prompt = "你是一位專業的分析師，請用繁體中文回答。回答要簡潔有力，重點條列。"

    # ═══ Round 1：獨立回答 ═══
    round1_prompt = f"請針對以下問題給出你的分析和建議（200字以內）：

{question}"

    # 三個 AI 同時回答
    r1_gemini, r1_llama, r1_cohere = await asyncio.gather(
        call_gemini(round1_prompt, system_prompt),
        call_llama(round1_prompt, system_prompt),
        call_cohere(round1_prompt, system_prompt),
        return_exceptions=True,
    )

    # 處理異常
    r1_gemini = str(r1_gemini) if isinstance(r1_gemini, Exception) else r1_gemini
    r1_llama = str(r1_llama) if isinstance(r1_llama, Exception) else r1_llama
    r1_cohere = str(r1_cohere) if isinstance(r1_cohere, Exception) else r1_cohere

    # ═══ Round 2：互相反駁/補充 ═══
    round2_prompt_template = """原始問題：{question}

以下是其他兩位 AI 的觀點：
---
觀點A：{opinion_a}
---
觀點B：{opinion_b}
---

請針對以上觀點進行反駁或補充（150字以內）。指出你認為對方觀點的不足之處，或補充遺漏的重點。"""

    r2_gemini_prompt = round2_prompt_template.format(
        question=question, opinion_a=r1_llama, opinion_b=r1_cohere
    )
    r2_llama_prompt = round2_prompt_template.format(
        question=question, opinion_a=r1_gemini, opinion_b=r1_cohere
    )
    r2_cohere_prompt = round2_prompt_template.format(
        question=question, opinion_a=r1_gemini, opinion_b=r1_llama
    )

    r2_gemini, r2_llama, r2_cohere = await asyncio.gather(
        call_gemini(r2_gemini_prompt, system_prompt),
        call_llama(r2_llama_prompt, system_prompt),
        call_cohere(r2_cohere_prompt, system_prompt),
        return_exceptions=True,
    )

    r2_gemini = str(r2_gemini) if isinstance(r2_gemini, Exception) else r2_gemini
    r2_llama = str(r2_llama) if isinstance(r2_llama, Exception) else r2_llama
    r2_cohere = str(r2_cohere) if isinstance(r2_cohere, Exception) else r2_cohere

    # ═══ Round 3：綜合結論 ═══
    round3_prompt = f"""原始問題：{question}

經過兩輪討論，以下是所有觀點的摘要：

【第一輪 - 獨立觀點】
🤖 Gemini：{r1_gemini}
🦙 Llama：{r1_llama}
⚡ Command R+：{r1_cohere}

【第二輪 - 反駁與補充】
🤖 Gemini：{r2_gemini}
🦙 Llama：{r2_llama}
⚡ Command R+：{r2_cohere}

請綜合以上所有觀點，產出一個最終的建議。要包含：
1. 最佳建議（考慮所有觀點後的結論）
2. 需要注意的風險或限制
3. 具體的行動步驟

請用 300 字以內完成。"""

    final_conclusion = await call_gemini(round3_prompt, "你是一位綜合分析師，請用繁體中文給出客觀、全面的最終建議。")

    # ═══ 組合最終輸出 ═══
    output = f"""🏆 AI 辯論結果
━━━━━━━━━━━━━━━
📝 問題：{question}

━━ Round 1：獨立觀點 ━━

🤖 Gemini：
{r1_gemini}

🦙 Llama：
{r1_llama}

⚡ Command R+：
{r1_cohere}

━━ Round 2：反駁與補充 ━━

🤖 Gemini：
{r2_gemini}

🦙 Llama：
{r2_llama}

⚡ Command R+：
{r2_cohere}

━━ Round 3：最終結論 ━━

🏆 綜合建議：
{final_conclusion}
━━━━━━━━━━━━━━━"""

    return output
