#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACK1_OUTPUT="${1:-${SCRIPT_DIR}/../../Track1/data/collected}"
DATA_ROOT="${2:-${SCRIPT_DIR}/data}"
TASK_KEY="${3:-}"

start_time=$(date +%s)
echo ">>> Track 2 started at: $(date)"
echo ">>> Track 1 output: ${TRACK1_OUTPUT}"
echo ">>> Track 2 data: ${DATA_ROOT}"

prepare_args=(--source "${TRACK1_OUTPUT}" --output "${DATA_ROOT}")
if [[ -n "${TASK_KEY}" ]]; then
    prepare_args+=(--task-key "${TASK_KEY}")
fi
python "${SCRIPT_DIR}/prepare_data.py" "${prepare_args[@]}"

EXEMPLAR2VQA_DATA_ROOT="${DATA_ROOT}" python "${SCRIPT_DIR}/1_extract_schema.py"

mapfile -t scenes < <(python -c "from pathlib import Path; p=Path(r'${DATA_ROOT}'); print('\\n'.join(sorted(x.name for x in p.iterdir() if x.is_dir() and (x / (x.name + '_bbox.json')).exists())))")
if [[ ${#scenes[@]} -eq 0 ]]; then
    echo "No prepared scenes were found in ${DATA_ROOT}."
    exit 1
fi

for scene_id in "${scenes[@]}"; do
    echo ">>> Processing ${scene_id}"
    EXEMPLAR2VQA_SCENE_ID="${scene_id}" EXEMPLAR2VQA_DATA_ROOT="${DATA_ROOT}" python "${SCRIPT_DIR}/2_architect_plan.py"
    EXEMPLAR2VQA_SCENE_ID="${scene_id}" EXEMPLAR2VQA_DATA_ROOT="${DATA_ROOT}" python "${SCRIPT_DIR}/3_coder_generate.py"
    EXEMPLAR2VQA_SCENE_ID="${scene_id}" EXEMPLAR2VQA_DATA_ROOT="${DATA_ROOT}" python "${SCRIPT_DIR}/4_code_refiner.py"
done

end_time=$(date +%s)
duration=$((end_time - start_time))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo "------------------------------------------------"
echo ">>> Track 2 completed in ${hours}h ${minutes}m ${seconds}s"
echo "------------------------------------------------"
