"""
Keyword definitions and matching logic for the research filter.

Two-tier filter:
  1. Paper must match at least one **agent** keyword.
  2. Paper must additionally match at least one **finance/audit** OR
     **pharma/medicine** keyword.
"""

from __future__ import annotations

import re


# ── Agent / Agentic AI keywords ─────────────────────────────────────────────
AGENT_KEYWORDS: list[str] = [
    r"\bagent\b",
    r"\bagents\b",
    r"\bmulti[\-\s]?agent\b",
    r"\bagentic\b",
    r"\bllm[\-\s]?agent\b",
    r"\bautonomous[\-\s]?agent\b",
    r"\btool[\-\s]?use\b",
    r"\btool[\-\s]?using\b",
    r"\bagent[\-\s]?framework\b",
    r"\breact\b",
    r"\bchain[\-\s]?of[\-\s]?thought[\-\s]?agent\b",
    r"\bagent[\-\s]?collaborat\w*\b",
    r"\bagent[\-\s]?orchestrat\w*\b",
    r"\bmulti[\-\s]?agent[\-\s]?system\b",
    r"\bagent[\-\s]?based\b",
    r"\bllm[\-\s]?based[\-\s]?agent\b",
    r"\breinforcement[\-\s]?learning[\-\s]?agent\b",
    r"\bagent[\-\s]?planning\b",
    r"\bagent[\-\s]?reasoning\b",
]

# ── Finance / Audit keywords ────────────────────────────────────────────────
FINANCE_AUDIT_KEYWORDS: list[str] = [
    r"\baudit\w*\b",
    r"\bfinancial\b",
    r"\bfinance\b",
    r"\baccounting\b",
    r"\bfraud[\-\s]?detect\w*\b",
    r"\bcompliance\b",
    r"\brisk[\-\s]?assess\w*\b",
    r"\binternal[\-\s]?control\b",
    r"\bassurance\b",
    r"\bforensic[\-\s]?account\w*\b",
    r"\bsox\b",
    r"\bsarbanes[\-\s]?oxley\b",
    r"\bregulat\w*\b",
    r"\banti[\-\s]?money[\-\s]?launder\w*\b",
    r"\baml\b",
    r"\bfinancial[\-\s]?report\w*\b",
    r"\bfinancial[\-\s]?statement\b",
    r"\btax\b",
    r"\btaxation\b",
]

# ── Pharma / Medicine keywords ──────────────────────────────────────────────
PHARMA_MEDICINE_KEYWORDS: list[str] = [
    r"\bpharmaceut\w*\b",
    r"\bdrug[\-\s]?discover\w*\b",
    r"\bclinical[\-\s]?trial\w*\b",
    r"\bpharmacolog\w*\b",
    r"\bmedical\b",
    r"\bhealthcare\b",
    r"\bhealth[\-\s]?care\b",
    r"\bbiomedic\w*\b",
    r"\bdrug[\-\s]?design\b",
    r"\bmolecul\w*\b",
    r"\bprotein\b",
    r"\bdiagnos\w*\b",
    r"\bpatient\b",
    r"\behr\b",
    r"\belectronic[\-\s]?health[\-\s]?record\b",
    r"\bdrug[\-\s]?repurpos\w*\b",
    r"\bdrug[\-\s]?development\b",
    r"\bclinical\b",
    r"\bpatholog\w*\b",
    r"\bradiol\w*\b",
    r"\boncolog\w*\b",
    r"\bgenomi\w*\b",
    r"\bprecision[\-\s]?medicine\b",
    r"\bmedic\w+[\-\s]?ai\b",
    r"\btherapeu\w*\b",
    r"\bbiomark\w*\b",
]

# ── Pre-compiled patterns (module-level, compiled once) ──────────────────────
_agent_re = [re.compile(p, re.IGNORECASE) for p in AGENT_KEYWORDS]
_finance_re = [re.compile(p, re.IGNORECASE) for p in FINANCE_AUDIT_KEYWORDS]
_pharma_re = [re.compile(p, re.IGNORECASE) for p in PHARMA_MEDICINE_KEYWORDS]


def _match_keywords(text: str, compiled: list[re.Pattern]) -> list[str]:
    """Return the *patterns* that matched inside *text*."""
    return [p.pattern for p in compiled if p.search(text)]


def matches_filter(title: str, abstract: str) -> dict | None:
    """Apply the two-tier keyword filter to a single paper.

    Returns a dict of matched keyword lists if the paper passes **both**
    tiers, otherwise ``None``.
    """
    combined = f"{title} {abstract}"
    agent_hits = _match_keywords(combined, _agent_re)
    if not agent_hits:
        return None

    finance_hits = _match_keywords(combined, _finance_re)
    pharma_hits = _match_keywords(combined, _pharma_re)
    if not finance_hits and not pharma_hits:
        return None

    return {
        "agent_keywords": agent_hits,
        "finance_keywords": finance_hits,
        "pharma_keywords": pharma_hits,
    }
