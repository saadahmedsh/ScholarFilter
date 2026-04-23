# Automated Research Pipeline

An automated, highly configurable pipeline designed to discover academic papers from major machine learning conferences based on flexible, dynamic keyword constraints.

## Architecture and Data Flow

The pipeline operates in three main stages:

1. **Fetch**: Papers are retrieved from external APIs. By default, it queries OpenReview for ICLR and NeurIPS, and Semantic Scholar (with a DBLP fallback mechanism) for AAAI.
2. **Deduplicate**: Papers are deduplicated across multiple sources and queries using normalized titles.
3. **Filter**: The pipeline uses a dynamically configurable multi-tier keyword filtering system. Papers are evaluated against groups defined in the configuration file. A paper is only accepted if it contains at least one keyword match from *every* defined group.

## Features

* **Modular Keyword Filtering**: Keyword criteria are no longer hardcoded. All search terms are consolidated into an extensible configuration file. Users can define arbitrary keyword groups.
* **Multi-source Integration**: Supports Semantic Scholar, DBLP, and OpenReview out of the box.
* **Structured Output**: Successfully filtered papers are exported to CSV and JSON formats, explicitly mapping the matching keywords for each group.
* **Centralized Configuration**: `config.yaml` controls all operational variables, API settings, search parameters, and keyword dictionaries.

## Prerequisites

* Python 3.11 or higher
* [uv](https://docs.astral.sh/uv/)

To install `uv`:

```bash
# macOS or Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup and Usage

1. Clone the repository and navigate to the project directory:

```bash
git clone <internal-repo-url>
cd internal-research-pipeline
```

2. Install dependencies:

```bash
uv sync
```

3. Run the pipeline:

```bash
uv run research-pipeline
```

Alternative execution via script wrappers:

```bash
# Linux or macOS
bash scripts/run.sh

# Windows (PowerShell)
.\scripts\run.ps1
```

## Configuration

The core of the system is managed by `config.yaml`.

### Key Configuration Sections

* **`output_dir`**: The directory path where the resulting CSV, JSON, and log files will be saved.
* **`keyword_groups`**: A dictionary where keys represent category names and values are lists of regex strings. A paper must match at least one string in every category to be included in the results.
* **`conferences`**: Contains sub-configurations for `openreview` (venues and labels) and `aaai` (search queries, maximum result limits, and fallback thresholds).
* **`api`**: Defines operational constraints (rate limits, timeouts, backoff durations) for Semantic Scholar, DBLP, and OpenReview.
* **`logging`**: Configures the desired output verbosity and log file destination.

### Environment Variables

Environment variables can override specific configuration parameters. Copy `.env.example` to `.env` to define them locally:

```bash
cp .env.example .env
```

* `SEMANTIC_SCHOLAR_API_KEY`: Increases rate limits for Semantic Scholar queries.
* `LOG_LEVEL`: Overrides the default logging verbosity (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`).

### Command Line Interface

The pipeline binary accepts optional flags to override paths at runtime:

```bash
uv run research-pipeline --config custom.yaml --output-dir ./custom-results
```

## Output Structure

Results are generated in the specified output directory (default: `output/`).

* `results.csv`: A flattened tabular representation of the matched papers, including dedicated columns for matched keywords from each configured group.
* `results.json`: A structured JSON document containing identical paper data.
* `pipeline.log`: An operational log detailing the fetch, deduplication, and filter processes.

## Project Layout

```text
internal-research-pipeline/
├── config.yaml               # Pipeline and keyword configuration
├── pyproject.toml            # Project manifest (uv)
├── .env.example              # Environment variable template
├── .gitignore
├── README.md                 # Project documentation
├── scripts/
│   ├── run.sh                # Execution script for UNIX
│   └── run.ps1               # Execution script for Windows
└── src/
    └── research_pipeline/
        ├── __init__.py
        ├── config.py         # Handles YAML parsing and environment overrides
        ├── keywords.py       # Implements dynamic group filtering logic
        └── pipeline.py       # Main controller for fetching and formatting
```
