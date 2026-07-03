from __future__ import annotations

from dataclasses import dataclass

from .budget import estimate_tokens
from .templates import fallback_action, fallback_rag_answer


@dataclass(frozen=True)
class LlmResult:
    text: str
    generated_by: str
    prompt_tokens: int
    completion_tokens: int


MAX_TOKENS = {
    "explain_priority": 300,
    "resident_notice": 400,
    "vendor_message": 500,
    "report": 1200,
    "rag_chat": 700,
}


def max_tokens_for(intent: str) -> int:
    return MAX_TOKENS.get(intent, 300)


async def compose_response(intent: str, card: dict[str, object], evidence: list[str], budget_allowed: bool) -> LlmResult:
    from ..config import get_settings

    settings = get_settings()
    prompt = f"{intent}\ncard={card}\nevidence={evidence}"
    if not settings.openai_api_key or not budget_allowed:
        fallback = fallback_action(intent, card, evidence)
        return LlmResult(
            text=fallback.text,
            generated_by="fallback:template",
            prompt_tokens=estimate_tokens(prompt),
            completion_tokens=estimate_tokens(fallback.text),
        )

    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, max_tokens=max_tokens_for(intent))
    response = await model.ainvoke(prompt)
    text = str(response.content)
    return LlmResult(
        text=text,
        generated_by=f"llm:{settings.openai_model}",
        prompt_tokens=estimate_tokens(prompt),
        completion_tokens=estimate_tokens(text),
    )


async def compose_rag_answer(question: str, evidence: list[str], budget_allowed: bool, context: str | None = None) -> LlmResult:
    from ..config import get_settings

    settings = get_settings()
    context_text = context or "선택된 운영 카드 없음"
    prompt = (
        "당신은 HeatGrid 운영 문서 RAG 답변 도우미입니다.\n"
        "규칙:\n"
        "1. 반드시 제공된 RAG 근거만 사용해 한국어로 답하세요.\n"
        "2. 근거에서 확인되지 않는 내용은 모른다고 말하세요.\n"
        "3. 답변 끝에 참고한 근거 번호를 짧게 적으세요.\n"
        f"\n운영 맥락:\n{context_text}\n\n질문:\n{question}\n\nRAG 근거:\n{evidence}"
    )
    if not settings.openai_api_key or not budget_allowed:
        fallback = fallback_rag_answer(question, evidence)
        return LlmResult(
            text=fallback,
            generated_by="fallback:template",
            prompt_tokens=estimate_tokens(prompt),
            completion_tokens=estimate_tokens(fallback),
        )

    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, max_tokens=max_tokens_for("rag_chat"))
    response = await model.ainvoke(prompt)
    text = str(response.content)
    return LlmResult(
        text=text,
        generated_by=f"llm:{settings.openai_model}",
        prompt_tokens=estimate_tokens(prompt),
        completion_tokens=estimate_tokens(text),
    )
