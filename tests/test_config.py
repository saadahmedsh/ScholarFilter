from research_pipeline.config import get_output_dir, load_config

def test_get_output_dir(tmp_path):
    d = tmp_path / "out"
    cfg = {"output_dir": str(d)}
    res = get_output_dir(cfg)
    assert res == d
    assert res.exists()

def test_load_config_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("output_dir: test_out\n", encoding="utf-8")

    cfg = load_config(cfg_path)
    assert cfg["output_dir"] == "test_out"

def test_load_config_env_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("logging:\n  level: INFO\n", encoding="utf-8")

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "abc12345")

    cfg = load_config(cfg_path)
    assert cfg["logging"]["level"] == "DEBUG"
    assert cfg["api"]["semantic_scholar"]["api_key"] == "abc12345"
