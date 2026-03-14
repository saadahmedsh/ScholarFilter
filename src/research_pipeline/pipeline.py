"""
Automated Research Pipeline
============================
Finds papers from AAAI 2025, NeurIPS 2025, and ICLR 2025 discussing
Agentic AI (Multi-Agent Systems, LLM Agents) in Financial Auditing
and Pharmaceuticals / Medicine.

Data sources:
  - ICLR 2025 & NeurIPS 2025  → OpenReview API
  - AAAI 2025                  → Semantic Scholar API (+ DBLP fallback)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from typing import Any

import pandas as pd
import requests
from tqdm import tqdm

from research_pipeline.config import get_output_dir, load_config
from research_pipeline.keywords import matches_filter

log = logging.getLogger(__name__)


def _setup_logging(cfg: dict[str, Any]) -> None:
    """Configure root logger with console + optional file handler."""
    level = getattr(logging, cfg.get("logging", {}).get("level", "INFO").upper(), logging.INFO)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    log_file = cfg.get("logging", {}).get("log_file")
    if log_file:
        out_dir = get_output_dir(cfg)
        fh = logging.FileHandler(out_dir / log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(fmt))
        handlers.append(fh)

    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)


def fetch_openreview_papers(
    venue_id: str,
    conference_label: str,
    cfg: dict[str, Any],
) -> list[dict]:
    """Fetch all accepted papers from an OpenReview venue."""
    try:
        import openreview  # type: ignore
    except ImportError:
        log.error("openreview-py is not installed. Run: uv add openreview-py")
        return []

    or_cfg = cfg.get("api", {}).get("openreview", {})
    base_url = or_cfg.get("base_url", "https://api2.openreview.net")

    log.info("Connecting to OpenReview for %s (%s) ...", conference_label, venue_id)
    client = openreview.api.OpenReviewClient(baseurl=base_url)

    all_notes: list = []
    try:
        log.info("  Fetching accepted papers from %s ...", venue_id)
        notes = client.get_all_notes(content={"venueid": venue_id}, details="original")
        all_notes = notes
        log.info("  Retrieved %d papers via venueid query.", len(all_notes))
    except Exception as e:
        log.warning("  venueid query failed: %s", e)
        for inv in [f"{venue_id}/-/Submission", f"{venue_id}/-/blind-submission"]:
            try:
                log.info("  Trying invitation: %s ...", inv)
                notes = client.get_all_notes(invitation=inv)
                if notes:
                    all_notes = notes
                    log.info("  Retrieved %d papers via invitation %s.", len(all_notes), inv)
                    break
            except Exception as e2:
                log.warning("  Invitation %s failed: %s", inv, e2)

    if not all_notes:
        log.warning("  No papers retrieved for %s.", conference_label)
        return []

    papers: list[dict] = []
    for note in tqdm(all_notes, desc=f"Processing {conference_label}"):
        content = note.content if hasattr(note, "content") else {}
        title = ""
        abstract = ""

        if isinstance(content.get("title"), dict):
            title = content["title"].get("value", "")
        elif isinstance(content.get("title"), str):
            title = content["title"]

        if isinstance(content.get("abstract"), dict):
            abstract = content["abstract"].get("value", "")
        elif isinstance(content.get("abstract"), str):
            abstract = content["abstract"]

        if not title:
            continue

        pdf_url = ""
        if hasattr(note, "id"):
            pdf_url = f"https://openreview.net/pdf?id={note.id}"

        papers.append({
            "Title": title,
            "Abstract": abstract,
            "PDF_URL": pdf_url,
            "Conference": conference_label,
        })

    log.info("  Fetched %d total papers from %s.", len(papers), conference_label)
    return papers


def _s2_search(
    query: str,
    venue: str,
    year: str,
    cfg: dict[str, Any],
    max_results: int = 2000,
) -> list[dict]:
    """Search Semantic Scholar for papers matching *query* + *venue* + *year*."""
    s2_cfg = cfg.get("api", {}).get("semantic_scholar", {})
    search_url = s2_cfg.get("search_url", "https://api.semanticscholar.org/graph/v1/paper/search")
    batch_limit = s2_cfg.get("batch_limit", 100)
    timeout = s2_cfg.get("request_timeout", 30)
    rate_sleep = s2_cfg.get("rate_limit_sleep", 1.5)
    rate_backoff = s2_cfg.get("rate_limit_backoff", 30)
    api_key = s2_cfg.get("api_key")

    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    papers: list[dict] = []
    offset = 0
    fields = "title,abstract,externalIds,url,venue,year,openAccessPdf"

    while offset < max_results:
        params = {
            "query": query,
            "venue": venue,
            "year": year,
            "limit": min(batch_limit, max_results - offset),
            "offset": offset,
            "fields": fields,
        }
        try:
            resp = requests.get(search_url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                log.warning("  Rate-limited by Semantic Scholar, waiting %ds ...", rate_backoff)
                time.sleep(rate_backoff)
                continue
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.warning("  Semantic Scholar request failed: %s", e)
            break

        batch = data.get("data", [])
        if not batch:
            break

        for p in batch:
            pdf_url = ""
            if p.get("openAccessPdf"):
                pdf_url = p["openAccessPdf"].get("url", "")
            if not pdf_url and p.get("externalIds", {}).get("DOI"):
                pdf_url = f"https://doi.org/{p['externalIds']['DOI']}"

            papers.append({
                "Title": p.get("title", ""),
                "Abstract": p.get("abstract", "") or "",
                "PDF_URL": pdf_url,
                "Conference": f"{venue} {year}",
            })

        total = data.get("total", 0)
        offset += len(batch)
        if offset >= total:
            break

        time.sleep(rate_sleep)

    return papers


def fetch_aaai_papers(cfg: dict[str, Any]) -> list[dict]:
    """Fetch AAAI 2025 papers via Semantic Scholar with multiple queries."""
    aaai_cfg = cfg.get("conferences", {}).get("aaai", {})
    venue = aaai_cfg.get("venue", "AAAI")
    year = aaai_cfg.get("year", "2025")
    queries = aaai_cfg.get("queries", ["agent"])
    max_per_query = aaai_cfg.get("max_results_per_query", 1000)
    inter_sleep = cfg.get("api", {}).get("semantic_scholar", {}).get("inter_query_sleep", 2)

    log.info("Fetching %s %s papers from Semantic Scholar ...", venue, year)

    all_papers: dict[str, dict] = {}
    for q in tqdm(queries, desc=f"{venue} S2 queries"):
        batch = _s2_search(query=q, venue=venue, year=year, cfg=cfg, max_results=max_per_query)
        for p in batch:
            key = p["Title"].strip().lower()
            if key not in all_papers:
                all_papers[key] = p
        time.sleep(inter_sleep)

    papers = list(all_papers.values())
    log.info("  Fetched %d unique %s %s papers from Semantic Scholar.", len(papers), venue, year)
    return papers


def fetch_aaai_dblp_fallback(cfg: dict[str, Any]) -> list[dict]:
    """Fallback: fetch AAAI 2025 papers from DBLP."""
    aaai_cfg = cfg.get("conferences", {}).get("aaai", {})
    dblp_cfg = cfg.get("api", {}).get("dblp", {})
    venue = aaai_cfg.get("venue", "AAAI")
    year = aaai_cfg.get("year", "2025")
    base_url = dblp_cfg.get("base_url", "https://dblp.org/search/publ/api")
    max_results = dblp_cfg.get("max_results", 1000)
    timeout = dblp_cfg.get("request_timeout", 30)
    inter_sleep = dblp_cfg.get("inter_query_sleep", 1)

    log.info("Fetching %s %s papers from DBLP (fallback) ...", venue, year)
    queries = ["agent", "multi-agent", "LLM agent", "agentic"]
    all_papers: dict[str, dict] = {}

    for q in tqdm(queries, desc=f"{venue} DBLP queries"):
        params = {
            "q": f"{q} venue:{venue} year:{year}",
            "format": "json",
            "h": max_results,
        }
        try:
            resp = requests.get(base_url, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.warning("  DBLP request failed: %s", e)
            continue

        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        for hit in hits:
            info = hit.get("info", {})
            title = info.get("title", "")
            url = info.get("ee", "") or info.get("url", "")
            key = title.strip().lower()
            if key not in all_papers:
                all_papers[key] = {
                    "Title": title,
                    "Abstract": "",
                    "PDF_URL": url,
                    "Conference": f"{venue} {year}",
                }
        time.sleep(inter_sleep)

    papers = list(all_papers.values())
    log.info("  Fetched %d unique %s %s papers from DBLP.", len(papers), venue, year)
    return papers


def _run_pipeline(cfg: dict[str, Any]) -> None:
    """Core pipeline logic: fetch → deduplicate → filter → save."""
    output_dir = get_output_dir(cfg)
    csv_path = output_dir / "results.csv"
    json_path = output_dir / "results.json"

    seen_titles: set[str] = set()
    matched: list[dict] = []
    total_fetched = 0
    total_unique = 0

    def process_papers(papers: list[dict]) -> None:
        nonlocal total_fetched, total_unique
        for p in papers:
            total_fetched += 1
            key = p["Title"].strip().lower()
            if key not in seen_titles:
                seen_titles.add(key)
                total_unique += 1
                result = matches_filter(p.get("Title", ""), p.get("Abstract", ""))
                if result:
                    p["Matched_Agent_Keywords"] = "; ".join(result["agent_keywords"])
                    p["Matched_Domain_Keywords"] = "; ".join(
                        result["finance_keywords"] + result["pharma_keywords"]
                    )
                    matched.append(p)

    for venue_cfg in cfg.get("conferences", {}).get("openreview", []):
        try:
            papers = fetch_openreview_papers(
                venue_cfg["venue_id"], venue_cfg["label"], cfg,
            )
            process_papers(papers)
        except Exception as exc:
            log.error("Failed to fetch %s: %s", venue_cfg.get("label"), exc)

    aaai_cfg = cfg.get("conferences", {}).get("aaai", {})
    dblp_threshold = aaai_cfg.get("dblp_fallback_threshold", 10)
    try:
        aaai = fetch_aaai_papers(cfg)
        if len(aaai) < dblp_threshold:
            log.info("Few results from Semantic Scholar — trying DBLP fallback …")
            aaai.extend(fetch_aaai_dblp_fallback(cfg))
        process_papers(aaai)
    except Exception as exc:
        log.error("Failed to fetch AAAI: %s", exc)

    log.info("Papers matching filters: %d", len(matched))

    columns = [
        "Title", "Abstract", "PDF_URL", "Conference",
        "Matched_Agent_Keywords", "Matched_Domain_Keywords",
    ]
    df = pd.DataFrame(matched, columns=columns)

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    log.info("CSV saved to: %s", csv_path)

    records = df.to_dict(orient="records")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    log.info("JSON saved to: %s", json_path)

    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total papers fetched (pre-dedup)         : {total_fetched}")
    print(f"  Total unique papers scanned (post-dedup) : {total_unique}")
    print(f"  Papers matching filter                   : {len(matched)}")
    print("  Breakdown by conference:")
    for conf_cfg in cfg.get("conferences", {}).get("openreview", []):
        label = conf_cfg["label"]
        count = len([p for p in matched if p["Conference"] == label])
        print(f"    {label}: {count}")
    aaai_label = f"{aaai_cfg.get('venue', 'AAAI')} {aaai_cfg.get('year', '2025')}"
    aaai_count = len([p for p in matched if p["Conference"] == aaai_label])
    print(f"    {aaai_label}: {aaai_count}")
    print("\n  Output files:")
    print(f"    CSV  : {csv_path}")
    print(f"    JSON : {json_path}")
    print("=" * 70)

    if matched:
        print("\n  Sample matched papers (up to 5):\n")
        for i, p in enumerate(matched[:5], 1):
            print(f"  [{i}] {p['Conference']}")
            print(f"      Title: {p['Title'][:100]}...")
            print(f"      PDF  : {p['PDF_URL'][:80]}")
            print()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="research-pipeline",
        description="Discover agentic-AI papers in finance/audit and pharma/medicine.",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="Path to config YAML (defaults to repo-root config.yaml).",
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

    _setup_logging(cfg)
    log.info("Agentic Research Scout v1.0.0 — starting pipeline")
    _run_pipeline(cfg)
    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()
