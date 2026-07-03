from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

ZIP_PATH = Path(__file__).resolve().parents[2] / "12_최종모델" / "m1_specialist_handoff.zip"


@pytest.mark.skipif(not ZIP_PATH.exists(), reason="handoff zip not available")
def test_handoff_agent_card_has_55_column_contract() -> None:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        with archive.open("m1_specialist_handoff/agent_contract/agent_state_card_schema.json") as handle:
            schema = json.loads(handle.read().decode("utf-8"))
        with archive.open("m1_specialist_handoff/agent_contract/agent_priority_card.csv") as handle:
            cards = pd.read_csv(handle)

    assert len(schema["columns"]) == 55
    assert list(cards.columns) == schema["columns"]
    assert len(cards) == 1226


@pytest.mark.skipif(not ZIP_PATH.exists(), reason="handoff zip not available")
def test_official_priority_uses_current_best_and_m1_specialist_weights() -> None:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        with archive.open("m1_specialist_handoff/agent_contract/agent_priority_card.csv") as handle:
            cards = pd.read_csv(handle)
    row = cards.iloc[0]
    expected = 0.65 * float(row["current_best_priority_score"]) + 0.35 * float(row["m1_specialist_priority_score"])
    assert float(row["priority_score"]) == pytest.approx(expected)
