import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0,1")
os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
import json
import re
import sys
import subprocess
import inspect
import logging

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
TRACK2_ROOT = os.path.abspath(os.path.join(AGENT_DIR, ".."))
REPOSITORY_ROOT = os.path.abspath(os.path.join(TRACK2_ROOT, ".."))
for import_path in (AGENT_DIR, TRACK2_ROOT, REPOSITORY_ROOT):
    if import_path not in sys.path:
        sys.path.append(import_path)
from shared.llm_backend import GenerationConfig, TextGenerationBackend
try:
    import Utils
except ImportError:
    print(f"[Error] Could not import Utils.py from {AGENT_DIR}")
    Utils = None
from Prompt import CoderPrompts

SCENE_ID = os.environ.get("EXEMPLAR2VQA_SCENE_ID", "scene_0")
DATA_ROOT = os.path.abspath(
    os.environ.get("EXEMPLAR2VQA_DATA_ROOT", os.path.join(AGENT_DIR, "data"))
)
MODEL_PATH = os.environ.get("EXEMPLAR2VQA_MODEL_PATH", "Qwen/Qwen3-Coder-30B-A3B-Instruct")

def get_utils_docstring():
    if Utils is None:
        return ""
    doc_lines = []
    for name, obj in inspect.getmembers(Utils):
        if inspect.isfunction(obj):
            try:
                sig = inspect.signature(obj)
                doc = inspect.getdoc(obj)
                doc_lines.append(f"def {name}{sig}:\n\"\"\"\n{doc}\n\"\"\"\n")
            except ValueError:
                continue
    return "\n".join(doc_lines)

def ensure_imports(code_text):
    """Ensure the response is clean Python and contains the required imports."""
    code_text = re.sub(r'^```python\w*\n', '', code_text, flags=re.MULTILINE)
    code_text = code_text.replace('```', '').strip()
    required_imports = [
        "import os",
        "import json",
        "import random",
        "import logging",
        "import math",
        "import numpy as np",
        "import re",
        "from collections import Counter",
        "from base_qa_generator import BaseQAGenerator",
        "from utils.common_utils import cal_3d_bbox_distance_between_categories",
        "from Utils import ("
    ]
    if "from base_qa_generator import BaseQAGenerator" not in code_text:
        utils_imports = [
            "    get_viewpoint_vectors, get_bbox_projection, is_spatial_relation_satisfied,",
            "    get_object_xz_points, filter_valid_scene_objects, calculate_planar_angles,",
            "    calculate_projected_distance, is_distance_valid, is_angle_ambiguous,",
            "    get_direction_label, get_visible_categories_per_view, calculate_target_view_index",
            ")"
        ]
        header = "\n".join(required_imports) + "\n" + "\n".join(utils_imports) + "\n\nlogger = logging.getLogger(__name__)\n\n"
        return header + code_text
    return code_text

def main():
    try:
        llm = TextGenerationBackend(MODEL_PATH, max_model_len=16384)
        print(f"=== {llm.backend} backend loaded successfully ===")
    except Exception as e:
        print(f"[Error] Model load failed: {e}")
        raise SystemExit(1)

    tasks_path = os.path.join(DATA_ROOT, SCENE_ID, "tasks.json")
    bbox_schema_path = os.path.join(DATA_ROOT, SCENE_ID, f"schema_{SCENE_ID}_bbox.json")
    view_schema_path = os.path.join(DATA_ROOT, SCENE_ID, f"schema_{SCENE_ID}_visible_views.json")

    if not os.path.exists(tasks_path):
        print(f"[Error] Tasks file not found: {tasks_path}")
        return

    with open(tasks_path, 'r') as f:
        tasks = json.load(f)
    max_tasks = int(os.environ.get("EXEMPLAR2VQA_MAX_TASKS", "0"))
    if max_tasks > 0:
        tasks = tasks[:max_tasks]

    bbox_schema = open(bbox_schema_path, 'r').read() if os.path.exists(bbox_schema_path) else "{}"
    view_schema = open(view_schema_path, 'r').read() if os.path.exists(view_schema_path) else "{}"
    utils_doc = get_utils_docstring()

    print("\n" + "="*20 + " PHASE 1: BATCH PROMPT PREPARATION " + "="*20)
    prompts = []
    task_names = []

    for task in tasks:
        task_name = task.get('task_name', 'unnamed_task')
        task_names.append(task_name)

        sys_msg = CoderPrompts.get_system_prompt()
        user_msg = CoderPrompts.get_user_prompt(task, bbox_schema, view_schema, utils_doc)
        messages = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]
        prompts.append(llm.format_chat(messages))

    print("\n" + "="*20 + " PHASE 2: CODE GENERATION " + "="*20)
    outputs = llm.generate_prompts(
        prompts,
        GenerationConfig(temperature=0.0, max_tokens=4096),
    )

    generated_scripts = []
    for i, raw_text in enumerate(outputs):
        task_name = task_names[i]

        match = re.search(r'```python\s*(.*?)```', raw_text, re.DOTALL)
        if match:
            raw_code = match.group(1).strip()
        else:
            raw_code = raw_text.strip()

        final_code = ensure_imports(raw_code)

        script_name = f"gen_{task_name}.py"
        script_path = os.path.join(DATA_ROOT, SCENE_ID, script_name)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(final_code)

        generated_scripts.append((task_name, script_name))
        print(f"✅ Generated and saved: {script_name}")

    print("\n" + "="*20 + " PHASE 3: SCRIPT TESTING " + "="*20)
    for task_name, script_name in generated_scripts:
        print(f"--- Testing {script_name} ---")
        cmd = [
            'python', script_name,
            '--processed_data_path', DATA_ROOT,
            '--dataset', 'holodeck',
            '--output_dir', os.path.join(DATA_ROOT, SCENE_ID),
            '--num_workers', '1'
        ]

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = (
                f"{TRACK2_ROOT}{os.pathsep}{AGENT_DIR}{os.pathsep}"
                f"{env.get('PYTHONPATH', '')}"
            )

            result = subprocess.run(
                cmd,
                cwd=os.path.join(DATA_ROOT, SCENE_ID),
                capture_output=True,
                text=True,
                env=env
            )

            if result.returncode == 0:
                print("✅ Execution Success! (Exit Code 0)")
                if result.stdout.strip():
                    for line in result.stdout.split('\n'):
                        if "DEBUG" in line or "Generated" in line or "Saved results" in line:
                            print(f"  {line}")

                expected_filename = f"qa_{task_name}_holodeck.json"
                output_full_path = os.path.join(DATA_ROOT, SCENE_ID, expected_filename)

                if os.path.exists(output_full_path):
                    with open(output_full_path, 'r') as f:
                        qa_data = json.load(f)
                    print(f"📊 Report: {len(qa_data)} valid QA pairs saved.")
                else:
                    print(f"❌ Output file NOT found (Usually means logic filtered all objects).")
            else:
                print("❌ Execution Failed! (Non-zero Exit Code)")
                print("--- STDERR ---")
                print(result.stderr.strip()[-1000:])
                print("--------------")
        except Exception as e:
            print(f"Subprocess Error: {e}")

        print("-" * 50)

if __name__ == "__main__":
    main()
