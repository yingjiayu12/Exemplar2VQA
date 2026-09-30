#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENES_ROOT="${1:-${ROOT_DIR}/Track1/data/scenes}"
TRACK1_OUTPUT="${2:-${ROOT_DIR}/Track1/data/collected}"
TRACK2_DATA="${3:-${ROOT_DIR}/Track2/Track2_pipeline/data}"
TASK_KEYS="${4:-all}"

bash "${ROOT_DIR}/Track1/Track1_Pipeline/run.sh" \
  "${SCENES_ROOT}" \
  "${TRACK1_OUTPUT}" \
  "${TASK_KEYS}"

TASK_FILTER=""
if [[ "${TASK_KEYS}" != "all" && "${TASK_KEYS}" != *,* ]]; then
  TASK_FILTER="${TASK_KEYS}"
fi

bash "${ROOT_DIR}/Track2/Track2_pipeline/run.sh" \
  "${TRACK1_OUTPUT}" \
  "${TRACK2_DATA}" \
  "${TASK_FILTER}"
