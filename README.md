Automated pipeline to discover **Agentic AI** papers (multi-agent systems, LLM agents, autonomous agents) applied to **Financial Auditing** and **Pharmaceuticals / Medicine** from top ML conferences.

## Features

- **Multi-source paper collection** — ICLR, NeurIPS (via OpenReview) and AAAI (via Semantic Scholar + DBLP fallback)
- **Two-tier keyword filtering** — requires both an "agent" keyword AND a domain keyword match
- **Structured output** — CSV and JSON with matched keywords per paper
- **Configurable** — all parameters in a single `config.yaml`
- **Logging** — console and file logging with configurable levels

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager

Install uv if you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Quick Start

```bash
# 1. Clone the repository
git clone <internal-repo-url>
cd internal-research-pipeline

# 2. Install dependencies
uv sync

# 3. Run the full pipeline
uv run research-pipeline
```

Or use the all-in-one script:

```bash
# Linux / macOS
bash scripts/run.sh

# Windows (PowerShell)
.\scripts\run.ps1
```

## Configuration

All settings are in [`config.yaml`](config.yaml). Key sections:

| Section | Purpose |
|---------|---------|
| `output_dir` | Where CSV, JSON, and logs are written |
| `conferences.openreview` | OpenReview venue IDs and labels |
| `conferences.aaai` | AAAI search queries and parameters |
| `api.semantic_scholar` | S2 rate limits, timeouts, API key |
| `api.dblp` | DBLP fallback settings |
| `logging` | Log level and log file name |

### Environment Variables

Copy `.env.example` to `.env` and fill in optional overrides:

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `SEMANTIC_SCHOLAR_API_KEY` | Higher rate limits on Semantic Scholar |
| `LOG_LEVEL` | Override log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### CLI Options

The pipeline supports `--config` and `--output-dir` overrides:

```bash
uv run research-pipeline --config custom.yaml --output-dir ./my-results
```

## Output

Results are written to the `output/` directory:

| File | Description |
|------|-------------|
| `results.csv` | All papers matching the keyword filter |
| `results.json` | Same data in JSON format |
| `pipeline.log` | Detailed execution log |

## Project Structure

```
agentic-research-scout/
├── config.yaml               # Pipeline configuration
├── pyproject.toml            # Project manifest (uv / pip)
├── .env.example              # Environment variable template
├── .gitignore
├── README.md
├── scripts/
│   ├── run.sh                # Bash automation script
│   └── run.ps1               # PowerShell automation script
└── src/
    └── research_pipeline/
        ├── __init__.py
        ├── config.py         # Config loader
        ├── keywords.py       # Keyword definitions and matching
        └── pipeline.py       # Main paper-fetching pipeline
```

## How It Works

1. **Fetch** — Collects papers from OpenReview (ICLR, NeurIPS) and Semantic Scholar/DBLP (AAAI)
2. **Filter** — Applies a two-tier keyword filter: papers must mention both an agent-related term AND a domain-specific term (finance/audit or pharma/medicine)
3. **Deduplicate** — Removes duplicate papers by normalised title

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run linting: `uv run ruff check .`
5. Submit a pull request
