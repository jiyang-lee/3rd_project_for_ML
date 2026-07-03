from __future__ import annotations

from heatgrid_ops.llm.templates import fallback_action


def test_template_fallback_generates_report_without_openai() -> None:
    result = fallback_action(
        "report",
        {
            "substation_id": "M1_31",
            "priority_tier": "urgent",
            "priority_score": 89.7,
            "risk_probability": 0.98,
            "fault_group": "leakage_water_loss",
            "why_reason": "risk high",
            "features": {"iforest_score_ratio": 0.96},
        },
        ["책임 구간 문서"],
    )
    assert result.ticket_intent == "internal"
    assert "M1_31" in result.text
    assert "leakage_water_loss" in result.text
