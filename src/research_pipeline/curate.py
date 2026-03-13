"""
Curate results — remove false positives from the pipeline output.

After careful manual review of every title + abstract, papers are removed if:
  1. "agent" refers only to an RL agent (not agentic AI / LLM agent)
  2. Domain keyword match is incidental (e.g. "accounting" = "taking into
     account", "protein" in a non-pharma context, etc.)
  3. The paper is not genuinely about agentic AI applied to finance/audit
     or pharma/medicine
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from research_pipeline.config import get_output_dir, load_config

log = logging.getLogger(__name__)


# ── Papers to KEEP (genuine agentic AI + finance/audit or pharma/medicine) ───
KEEP_TITLES: set[str] = {
    # === Genuinely Agentic AI + Medicine/Pharma ===
    "KGARevion: An AI Agent for Knowledge-Intensive Biomedical QA",
    "PathGen-1.6M: 1.6 Million Pathology Image-text Pairs Generation through Multi-agent Collaboration",
    "BioDiscoveryAgent: An AI Agent for Designing Genetic Perturbation Experiments",
    "OSDA Agent: Leveraging Large Language Models for De Novo Design of Organic Structure Directing Agents",
    "CPathAgent: An Agent-based Foundation Model for Interpretable High-Resolution Pathology Image Analysis Mimicking Pathologists' Diagnostic Logic",
    "Towards Doctor-Like Reasoning: Medical RAG Fusing Knowledge with Patient Analogy through Textual Gradients",
    "MoodAngels: A Retrieval-augmented Multi-agent Framework for Psychiatry Diagnosis",
    "SiriuS: Self-improving Multi-agent Systems via Bootstrapped Reasoning",
    "Retro-R1: LLM-based Agentic Retrosynthesis",
    "SPASCA: Social Presence and Support with Conversational Agent for Persons Living with Dementia",
    "Multi-OphthaLingua: A Multilingual Benchmark for Assessing and Debiasing LLM Ophthalmological QA in LMICs",
    "Like an Ophthalmologist: Dynamic Selection Driven Multi-View Learning for Diabetic Retinopathy Grading",
    "DyFlow: Dynamic Workflow Framework for Agentic Reasoning",
    "Conformal Information Pursuit for Interactively Guiding Large Language Models",
    "4KAgent: Agentic Any Image to 4K Super-Resolution",
    # === Genuinely Agentic AI + Finance/Audit ===
    "InsightBench: Evaluating Business Analytics Agents Through Multi-Step Insight Generation",
    "MarS: a Financial Market Simulation Engine Powered by Generative Foundation Model",
    "Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents",
    "InvestESG: A multi-agent reinforcement learning benchmark for studying climate investment as a social dilemma",
    "TwinMarket: A Scalable Behavioral and Social Simulation for Financial Markets",
    "OPHR: Mastering Volatility Trading with Multi-Agent Deep Reinforcement Learning",
    "Robust Reinforcement Learning in Finance:  Modeling Market Impact with Elliptic Uncertainty Sets",
    "CALM: Curiosity-Driven Auditing for Large Language Models",
    "Augmented Lagrangian Risk-constrained Reinforcement Learning for Portfolio Optimization (Student Abstract)",
    "Encoder of Thoughts: Enhancing Planning Ability in Language Agents Through Structural Embedding",
    "TimeCAP: Learning to Contextualize, Augment, and Predict Time Series Events with Large Language Model Agents",
    "AutoData: A Multi-Agent System for Open Web Data Collection",
}

# ── Papers to REMOVE (false positives) with reasons ─────────────────────────
REMOVE_TITLES_WITH_REASONS: dict[str, str] = {
    "When LLMs Play the Telephone Game: Cultural Attractors as Conceptual Tools to Evaluate LLMs in Multi-turn Settings":
        "FP: 'accounting' used as 'accounting for' (phrasal), not financial accounting",
    "Anyprefer: An Agentic Framework for Preference Data Synthesis":
        "FP: 'medical' is incidental - framework is for preference data synthesis",
    "Audio Large Language Models Can Be Descriptive Speech Quality Evaluators":
        "FP: 'audit' matched 'auditory' - paper about speech quality evaluation",
    "Steering Masked Discrete Diffusion Models via Discrete Denoising Posterior Prediction":
        "FP: 'agents' refers to text-based agents, 'protein' about protein sequence design",
    "Robotouille: An Asynchronous Planning Benchmark for LLM Agents":
        "FP: 'audit' matched 'self-audit' - paper about robot planning",
    "Sample-Efficient Tabular Self-Play for Offline Robust Reinforcement Learning":
        "FP: 'multi-agent' is MARL theory, 'accounting' = 'accounting for' (phrasal)",
    "STRIDER: Navigation via Instruction-Aligned Structural Decision Space Optimization":
        "FP: 'agents' = navigation agents, 'regulat*' matched 'Regulator' component",
    "Knowledge Starts with Practice: Knowledge-Aware Exercise Generative Recommendation with Adaptive Multi-Agent Cooperation":
        "FP: 'diagnos*' matched 'diagnose' in educational context",
    "Social World Model-Augmented Mechanism Design Policy Learning":
        "FP: 'tax' = Pigovian tax in RL/mechanism design context",
    "Enhancing Personalized Multi-Turn Dialogue with Curiosity Reward":
        "FP: 'healthcare' is incidental mention",
    "A Snapshot of Influence: A Local Data Attribution Framework for Online Reinforcement Learning":
        "FP: 'diagnos*' matched 'diagnosis of learning' in RL context",
    "What do you know? Bayesian knowledge inference for navigating agents":
        "FP: 'accounting' = 'accounting for uncertainty', navigation agents",
    "Strategic Hypothesis Testing":
        "FP: 'agent' is principal-agent economic framework, not agentic AI",
    "Attractive Metadata Attack: Inducing LLM Agents to Invoke Malicious Tools":
        "FP: 'audit*' matched 'auditor-based detection' - paper about LLM security",
    "Securing the Language of Life: Inheritable Watermarks from DNA Language Models to Proteins":
        "FP: 'agents' = biological agents, not agentic AI",
    "STRATUS: A Multi-agent System for Autonomous Reliability Engineering of Modern Clouds":
        "FP: domain is cloud SRE, not finance/pharma",
    "LOPT: Learning Optimal Pigovian Tax in Sequential Social Dilemmas":
        "FP: 'tax' = Pigovian tax in MARL theory",
    "Efficient Safe Meta-Reinforcement Learning: Provable Near-Optimality and Anytime Safety":
        "FP: 'compliance' = safety compliance in RL",
    "Stable Gradients for Stable Learning at Scale in Deep Reinforcement Learning":
        "FP: 'patholog*' matched 'gradient pathologies', 'agents' = RL agents",
    "Breaking the Performance Ceiling in Reinforcement Learning requires Inference Strategies":
        "FP: 'protein' is incidental mention",
    "Deep RL Needs Deep Behavior Analysis: Exploring Implicit Planning by Model-Free Agents in Open-Ended Environments":
        "FP: 'diagnos*' matched 'diagnostic methods' for RL behavior analysis",
    "Adaptable Safe Policy Learning from Multi-task Data with Constraint Prioritized Decision Transformer":
        "FP: 'compliance' = safety compliance in offline RL",
    "DesignX: Human-Competitive Algorithm Designer for Black-Box Optimization":
        "FP: 'protein' is incidental mention as one optimization scenario",
    "WALL-E: World Alignment by NeuroSymbolic Learning improves World Model-based LLM Agents":
        "FP: 'regulat*' matched 'regulate' - paper about world models for Minecraft",
    "NFL-BA: Near-Field Light Bundle Adjustment for SLAM in Dynamic Lighting":
        "FP: 'patient' is incidental, paper about SLAM/lighting",
    "Consistently Simulating Human Personas with Multi-Turn Reinforcement Learning":
        "FP: 'patient' = one simulated persona",
    "CoP: Agentic Red-teaming for Large Language Models using Composition of Principles":
        "FP: 'compliance' = 'user compliance' in LLM safety context",
    "How to Train Your LLM Web Agent: A Statistical Diagnosis":
        "FP: 'diagnos*' in title means statistical diagnosis of training",
    "Cognitive Predictive Processing: A Human-inspired Framework for Adaptive Exploration in Open-World Reinforcement Learning":
        "FP: 'regulat*' matched 'regulator' module, paper about RL exploration",
    "Uncover Governing Law of Pathology Propagation Mechanism Through A Mean-Field Game":
        "FP: 'agent' = mean-field game agents (mathematical), not agentic AI",
    "VLMLight: Safety-Critical Traffic Signal Control via Vision-Language Meta-Control and Dual-Branch Reasoning Architecture":
        "FP: 'compliance' = rule compliance in traffic control",
    "Multi-Agent Security Tax: Trading Off Security and Collaboration Capabilities in Multi-Agent Systems":
        "FP: 'tax' = metaphorical 'security tax'",
    "Alleviate and Mining: Rethinking Unsupervised Domain Adaptation for Mitochondria Segmentation from Pseudo-Label Perspective":
        "FP: 'agent' = 'agent-level correlations', not agentic AI",
    "On Corruption-Robustness in Performative Reinforcement Learning":
        "FP: 'accounting' = 'accounting for corruption', RL theory",
    "Active Reinforcement Learning Strategies for Offline Policy Improvement":
        "FP: 'medical' = incidental mention of medical trials",
    "ASP-Driven Emergency Planning for Norm Violations in Reinforcement Learning":
        "FP: 'healthcare' = incidental mention as one application",
    "Explicit and Implicit Examinee-Question Relation Exploiting for Efficient Computerized Adaptive Testing":
        "FP: 'diagnos*' matched 'diagnose examinees' ability' - educational",
    "Breaking the Resource Monopoly from Industries: Sustainable and Reliable LLM Serving by Recycling Outdated and Resource-Constrained GPUs":
        "FP: 'financial' = 'financial pressures', paper about GPU recycling",
}


def _run_curation(cfg: dict[str, Any], input_path: Path | None = None) -> None:
    """Core curation logic: load → classify → save curated set."""
    output_dir = get_output_dir(cfg)

    src = input_path or (output_dir / "results.json")
    if not src.exists():
        log.error("Input file not found: %s", src)
        log.error("Run 'research-pipeline' first to generate results.")
        raise SystemExit(1)

    with open(src, "r", encoding="utf-8") as f:
        papers = json.load(f)

    kept: list[dict] = []
    removed: list[tuple[dict, str]] = []
    unclassified: list[dict] = []

    for p in papers:
        title = p["Title"]
        if title in KEEP_TITLES:
            kept.append(p)
        elif title in REMOVE_TITLES_WITH_REASONS:
            removed.append((p, REMOVE_TITLES_WITH_REASONS[title]))
        else:
            unclassified.append(p)

    log.info("Original papers: %d", len(papers))
    log.info("Kept:            %d", len(kept))
    log.info("Removed:         %d", len(removed))
    log.info("Unclassified:    %d", len(unclassified))

    if unclassified:
        log.warning("⚠ UNCLASSIFIED papers (need review):")
        for p in unclassified:
            log.warning("  - %s", p["Title"])

    # Write curated outputs
    curated_csv = output_dir / "curated_results.csv"
    curated_json = output_dir / "curated_results.json"

    columns = [
        "Title", "Abstract", "PDF_URL", "Conference",
        "Matched_Agent_Keywords", "Matched_Domain_Keywords",
    ]
    df = pd.DataFrame(kept, columns=columns)
    df.to_csv(curated_csv, index=False, encoding="utf-8-sig")
    log.info("Curated CSV  saved to: %s", curated_csv)

    with open(curated_json, "w", encoding="utf-8") as f:
        json.dump(kept, f, indent=2, ensure_ascii=False)
    log.info("Curated JSON saved to: %s", curated_json)

    # Summary
    print(f"\n{'=' * 70}")
    print("  CURATED RESULTS")
    print(f"{'=' * 70}")
    print(f"  Papers kept: {len(kept)}")
    print("  Breakdown by conference:")
    for conf in ["ICLR 2025", "NeurIPS 2025", "AAAI 2025"]:
        count = len([p for p in kept if p["Conference"] == conf])
        print(f"    {conf}: {count}")
    print("\n  All kept papers:")
    for i, p in enumerate(kept, 1):
        print(f"    [{i:>2}] [{p['Conference']}] {p['Title']}")
    print(f"\n  Removed {len(removed)} false positives")
    print(f"{'=' * 70}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="curate-results",
        description="Remove false positives from the research pipeline output.",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="Path to config YAML (defaults to repo-root config.yaml).",
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Path to the input results.json (defaults to output_dir/results.json).",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Override the output directory from config.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    cfg = load_config(args.config)

    if args.output_dir:
        cfg["output_dir"] = args.output_dir

    level = getattr(
        logging,
        cfg.get("logging", {}).get("level", "INFO").upper(),
        logging.INFO,
    )
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )

    input_path = Path(args.input) if args.input else None
    log.info("Agentic Research Scout — curating results")
    _run_curation(cfg, input_path)
    log.info("Curation complete.")


if __name__ == "__main__":
    main()
