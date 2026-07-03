from __future__ import annotations

from heatgrid_ops.llm.budget import estimate_tokens
from heatgrid_ops.llm.cache import cache_key


def test_cache_key_changes_when_card_hash_changes() -> None:
    first = cache_key("report", 1, "a")
    second = cache_key("report", 1, "b")
    assert first != second
    assert len(first) == 64


def test_estimate_tokens_has_lower_bound() -> None:
    assert estimate_tokens("") == 1
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcdefgh") == 2
