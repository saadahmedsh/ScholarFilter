"""
Keyword definitions and matching logic for the research filter.
"""

from __future__ import annotations

import re
from typing import Any


class KeywordFilter:
    """A filter for matching papers against dynamic keyword groups."""

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize the filter with compiled regular expressions from the configuration."""
        self.groups: dict[str, list[re.Pattern]] = {}
        for group_name, keywords in cfg.get("keyword_groups", {}).items():
            self.groups[group_name] = [re.compile(p, re.IGNORECASE) for p in keywords]

    def _match_keywords(self, text: str, compiled: list[re.Pattern]) -> list[str]:
        """Return the patterns that matched inside the provided text."""
        return [p.pattern for p in compiled if p.search(text)]

    def matches(self, title: str, abstract: str) -> dict[str, list[str]] | None:
        """Apply the dynamic keyword group filter to a single paper.

        Args:
            title: The title of the paper.
            abstract: The abstract of the paper.

        Returns:
            A dictionary mapping group names to matched keyword lists if the paper
            passes the filter by matching at least one keyword in every group.
            Returns None if any group has no matches.
        """
        if not self.groups:
            return None

        combined: str = f"{title} {abstract}"
        results: dict[str, list[str]] = {}

        for group_name, compiled_re in self.groups.items():
            hits: list[str] = self._match_keywords(combined, compiled_re)
            if not hits:
                return None
            results[group_name] = hits

        return results


def matches_filter(title: str, abstract: str, cfg: dict[str, Any]) -> dict[str, list[str]] | None:
    """Apply the dynamic keyword group filter to a single paper (legacy interface)."""
    return KeywordFilter(cfg).matches(title, abstract)
