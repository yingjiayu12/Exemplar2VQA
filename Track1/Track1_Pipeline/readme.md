# Track 1: Camera Generation

Track 1 turns natural-language capture instructions into executable AI2-THOR camera programs, runs them on Holodeck-compatible scene JSON files, and reviews failed trajectories.

## Files

- `Instructions.py` defines one or more camera-collection tasks.
- `camera_skills.py` provides deterministic scene, geometry, capture, and serialization APIs.
- `run_camera_agent.py` plans, generates, and executes camera code.
- `run_camera_reviewer.py` reviews failures and iteratively refines generated code.
- `run.sh` is the portable entry point.

## Usage

Run from any directory:

```bash
bash Track1/Track1_Pipeline/run.sh [SCENES_ROOT] [OUTPUT_DIR] [TASK_KEYS]
```

All arguments are optional. Defaults are `Track1/data/scenes`, `Track1/data/collected`, and `all`. `TASK_KEYS` accepts a comma-separated list such as `A,B`.
