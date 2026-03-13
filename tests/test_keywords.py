from research_pipeline.keywords import matches_filter

def test_matches_filter_no_match():
    # Neither agent nor domain
    assert matches_filter("Hello world", "This is a simple test.") is None

    # Only agent, no domain
    assert matches_filter("A novel LLM agent", "It performs well on benchmarks.") is None

    # Only domain, no agent
    assert matches_filter("Audit reporting standards", "A discussion on financial risk.") is None

def test_matches_filter_both():
    res = matches_filter("Audit reporting with a multi-agent system", "A discussion on financial risk and agents.")
    assert res is not None
    assert len(res["agent_keywords"]) > 0
    assert len(res["finance_keywords"]) > 0
    assert len(res["pharma_keywords"]) == 0
