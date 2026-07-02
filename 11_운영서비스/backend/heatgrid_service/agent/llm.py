"""OpenAI LLM 래퍼 — 키가 없으면 None을 반환해 모든 노드가 템플릿 폴백으로 동작."""

from __future__ import annotations

import logging
from functools import lru_cache

from ..config import get_settings

logger = logging.getLogger("heatgrid.agent.llm")


@lru_cache(maxsize=1)
def get_llm():
    settings = get_settings()
    if not settings.openai_api_key:
        logger.info("OPENAI_API_KEY 미설정 — 템플릿 폴백 모드로 동작")
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0.2)


def llm_text(prompt: str) -> str | None:
    llm = get_llm()
    if llm is None:
        return None
    try:
        return llm.invoke(prompt).content
    except Exception:
        logger.exception("LLM 호출 실패 — 폴백 사용")
        return None
