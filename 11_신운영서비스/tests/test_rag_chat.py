from __future__ import annotations

from heatgrid_ops.api.queries import RagChatRequest, rag_search_patterns
from heatgrid_ops.llm.templates import fallback_rag_answer


def test_rag_search_patterns_split_question_keywords() -> None:
    patterns = rag_search_patterns("열사용시설 책임 범위 알려줘")

    assert "%열사용시설%" in patterns
    assert "%책임%" in patterns
    assert "%범위%" in patterns


def test_rag_chat_request_keeps_card_context_out_of_search_terms() -> None:
    request = RagChatRequest(question="책임 구간", context="M1_30 leakage_water_loss urgent")

    assert rag_search_patterns(request.question) == ["%책임%", "%구간%"]


def test_fallback_rag_answer_uses_retrieved_sources() -> None:
    answer = fallback_rag_answer(
        "책임 범위 알려줘",
        ["[1] 열사용시설 기준\n사용자 시설과 공급자 시설의 책임 구간을 구분한다."],
    )

    assert "책임 범위 알려줘" in answer
    assert "사용자 시설과 공급자 시설" in answer
    assert "근거" in answer
