#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENES_ROOT="${1:-${SCRIPT_DIR}/../data/scenes}"
OUTPUT_DIR="${2:-${SCRIPT_DIR}/../data/collected}"
TASK_KEYS="${3:-all}"

start_time=$(date +%s)
echo ">>> Track 1 started at: $(date)"
echo ">>> Scenes: ${SCENES_ROOT}"
echo ">>> Output: ${OUTPUT_DIR}"

python "${SCRIPT_DIR}/run_camera_agent.py" \
    --scenes_root "${SCENES_ROOT}" \
    --output_dir "${OUTPUT_DIR}" \
    --task_keys "${TASK_KEYS}"

python "${SCRIPT_DIR}/run_camera_reviewer.py" \
    --scenes_root "${SCENES_ROOT}" \
    --output_dir "${OUTPUT_DIR}" \
    --task_keys "${TASK_KEYS}"

end_time=$(date +%s)
duration=$((end_time - start_time))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo "------------------------------------------------"
echo ">>> Track 1 completed in ${hours}h ${minutes}m ${seconds}s"
echo "------------------------------------------------"
