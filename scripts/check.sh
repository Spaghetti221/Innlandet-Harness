#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
OFFLINE=${1:-}

python3 harness/probe.py $OFFLINE
python3 eval/check_probe.py
claude -p "$(cat harness/prompts/summarise.md)" \
--permission-mode dontAsk \
--allowedTools "Read,Edit(/out/**)"
python3 eval/check_summary.py
