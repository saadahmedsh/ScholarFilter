#!/usr/bin/env bash
# =============================================================================
# Agentic Research Scout — Run Script
# =============================================================================
# Usage:  ./scripts/run.sh [--config path/to/config.yaml]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Colour

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Agentic Research Scout                               ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

# ── 1. Check uv is installed ────────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv is not installed. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "${GREEN}uv installed successfully.${NC}"
fi

# ── 2. Install / sync dependencies ──────────────────────────────────────────
echo -e "\n${YELLOW}[1/3] Syncing dependencies...${NC}"
uv sync

# ── 3. Run the pipeline ─────────────────────────────────────────────────────
echo -e "\n${YELLOW}[2/2] Running research pipeline...${NC}"
uv run research-pipeline "$@"

echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Done! Check the output/ directory for results.       ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
