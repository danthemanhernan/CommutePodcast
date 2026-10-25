#!/usr/bin/env bash
set -euo pipefail

uv run commute-podcast generate-all --publish "$@"
