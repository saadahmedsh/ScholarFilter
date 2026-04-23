from research_pipeline.keywords import KeywordFilter  # type: ignore  # type: ignore
from typing import Any

mock_cfg: dict[str, Any] = {
    "keyword_groups": {
        "Agent": [r"\bagent\b", r"\bllm agent\b", r"\bmulti[\-\s]?agent\b"],
        "Domain": [r"\baudit\w*\b", r"\bfinancial\b", r"\brisk\b"]
    }
}

def test_matches_filter_no_match():
    assert KeywordFilter(mock_cfg).matches("Hello world", "This is a simple test.") is None
    assert KeywordFilter(mock_cfg).matches("A novel LLM agent", "It performs well on benchmarks.") is None
    assert KeywordFilter(mock_cfg).matches("Audit reporting standards", "A discussion on financial risk.") is None

def test_matches_filter_both():
    res = KeywordFilter(mock_cfg).matches("Audit reporting with a multi-agent system", "A discussion on financial risk and agents.")
    assert res is not None
    assert "Agent" in res
    assert len(res["Agent"]) > 0
    assert "Domain" in res
    assert len(res["Domain"]) > 0
