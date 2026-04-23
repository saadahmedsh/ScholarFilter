"""
Configuration loader for the Automated Research Pipeline.

Loads settings from a YAML file, merges with environment variable overrides,
and provides typed access to all pipeline parameters.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG_PATH: Path = Path(__file__).resolve().parent.parent.parent / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """
    Load configuration from the specified path.

    Args:
        path: Path to the YAML configuration file. Defaults to config.yaml.

    Returns:
        A dictionary containing the pipeline configuration parameters.

    Raises:
        FileNotFoundError: If the configuration file is not found.
    """
    config_path: Path = Path(path) if path else _DEFAULT_CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Ensure config.yaml is present in the expected location."
        )

    with open(config_path, "r", encoding="utf-8") as fh:
        cfg: dict[str, Any] = yaml.safe_load(fh) or {}

    if os.getenv("LOG_LEVEL"):
        cfg.setdefault("logging", {})["level"] = str(os.environ.get("LOG_LEVEL"))

    if os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
        cfg.setdefault("api", {}).setdefault("semantic_scholar", {})[
            "api_key"
        ] = str(os.environ.get("SEMANTIC_SCHOLAR_API_KEY"))

    return cfg


def get_output_dir(cfg: dict[str, Any]) -> Path:
    """
    Return the resolved output directory, creating it if needed.

    Args:
        cfg: The configuration dictionary containing the output_dir parameter.

    Returns:
        The Path object representing the output directory.
    """
    out: Path = Path(cfg.get("output_dir", "./output"))
    out.mkdir(parents=True, exist_ok=True)
    return out
