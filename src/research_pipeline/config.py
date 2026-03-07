"""
Configuration loader for Agentic Research Scout.

Loads settings from a YAML file, merges with environment variable overrides,
and provides typed access to all pipeline parameters.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from *path* (defaults to repo-root ``config.yaml``).

    Environment variable overrides
    ──────────────────────────────
    * ``LOG_LEVEL``  → ``logging.level``
    * ``SEMANTIC_SCHOLAR_API_KEY`` → ``api.semantic_scholar.api_key``
    """
    config_path = Path(path) if path else _DEFAULT_CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Copy config.yaml.example or create one — see README.md."
        )

    with open(config_path, "r", encoding="utf-8") as fh:
        cfg: dict[str, Any] = yaml.safe_load(fh) or {}

    # ── Env-var overrides ────────────────────────────────────────────────
    if os.getenv("LOG_LEVEL"):
        cfg.setdefault("logging", {})["level"] = os.environ["LOG_LEVEL"]

    if os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
        cfg.setdefault("api", {}).setdefault("semantic_scholar", {})[
            "api_key"
        ] = os.environ["SEMANTIC_SCHOLAR_API_KEY"]

    return cfg


def get_output_dir(cfg: dict[str, Any]) -> Path:
    """Return the resolved output directory, creating it if needed."""
    out = Path(cfg.get("output_dir", "./output"))
    out.mkdir(parents=True, exist_ok=True)
    return out
