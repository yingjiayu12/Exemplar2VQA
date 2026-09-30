import os
import sys
import json
import re
import subprocess
import gc
from argparse import ArgumentParser
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0,1")
os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
from Prompt import CameraArchitectPrompts, CameraCoderPrompts
from Instructions import CameraInstructions

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
REPOSITORY_ROOT = os.path.abspath(os.path.join(PIPELINE_DIR, "..", ".."))
if REPOSITORY_ROOT not in sys.path:
    sys.path.append(REPOSITORY_ROOT)
from shared.llm_backend import GenerationConfig, TextGenerationBackend

DEFAULT_SCENES_ROOT = os.path.abspath(os.path.join(PIPELINE_DIR, "..", "data", "scenes"))
DEFAULT_OUTPUT_DIR = os.path.abspath(os.path.join(PIPELINE_DIR, "..", "data", "collected"))
MODEL_PATH = os.environ.get("EXEMPLAR2VQA_MODEL_PATH", "Qwen/Qwen3-Coder-30B-A3B-Instruct")

def extract_json_from_text(text):
    """Safely extract a JSON list from an LLM response."""
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
        json_str = match.group(0) if match else text

    try:
        return json.loads(json_str)
    except Exception as e:
        print(f"[Error] Failed to parse JSON: {e}\nRaw String:\n{json_str}")
        return None

def extract_python_from_text(text):
    """Extract Python code from an LLM response."""
    match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

def build_runner_script(generated_class_code, class_name, task_meta):
    thor_runner_template = f"""
{generated_class_code}

# ==============================================================================
# [AUTO-GENERATED RUNNER] AI2-THOR Controller Initialization & Execution
# ==============================================================================
if __name__ == "__main__":
    import argparse
    import compress_json
    import os
    import sys

    # Generated scripts are stored under gen_code/<task_key>.
    # Two parent levels above the generated script is the Track 1 pipeline.
    CURRENT_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    TRACK1_ROOT = os.path.abspath(os.path.join(CURRENT_APP_DIR, ".."))
    REPOSITORY_PARENT = os.path.abspath(os.path.join(TRACK1_ROOT, "..", ".."))
    HOLODECK_ROOT = os.environ.get(
        "HOLODECK_ROOT", os.path.join(REPOSITORY_PARENT, "Holodeck")
    )

    for import_path in (TRACK1_ROOT, CURRENT_APP_DIR, HOLODECK_ROOT):
        if os.path.isdir(import_path) and import_path not in sys.path:
            sys.path.append(import_path)

    from natsort import natsorted
    from ai2thor.controller import Controller
    from ai2thor.hooks.procedural_asset_hook import ProceduralAssetHookRunner
    from ai2thor.platform import CloudRendering

    from ai2holodeck.constants import OBJATHOR_ASSETS_DIR

    from camera_skills import CameraSkills

    parser = argparse.ArgumentParser()
    parser.add_argument("--scenes_root", required=True)
    parser.add_argument("--asset_dir", default=OBJATHOR_ASSETS_DIR)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    # 1. Discover scene files
    scene_files = []
    if os.path.isfile(args.scenes_root):
        scene_files.append(args.scenes_root)
    else:
        for root, dirs, files in os.walk(args.scenes_root):
            for file in files:
                if file.endswith(".json") and "_bbox.json" not in file and "_views.json" not in file:
                    scene_files.append(os.path.join(root, file))

    try:
        scene_files = natsorted(scene_files)
    except:
        scene_files.sort()

    if not scene_files:
        print("No scene files found!")
        exit(1)

    print(f"Found {{len(scene_files)}} scenes. Initializing AI2-THOR Controller...")

    # 2. Initialize the controller
    controller = Controller(
        scene="Procedural",
        agentMode="default",
        gridSize=0.25,
        width=1024,
        height=768,
        visibilityDistance=200.0,
        renderInstanceSegmentation=True,
        makeAgentsVisible=False,
        visibilityScheme="Distance",
        action_hook_runner=ProceduralAssetHookRunner(
            asset_directory=args.asset_dir,
            asset_symlink=True,
            verbose=False,
        ),
        platform=CloudRendering,
        server_timeout=500
    )

    # 3. Initialize CameraSkills and the agent-generated trajectory class
    skills = CameraSkills(controller)
    trajectory_worker = {class_name}(skills)

    # 4. Iterate over scenes and collect observations
    for idx, scene_path in enumerate(scene_files):
        scene_name = os.path.splitext(os.path.basename(scene_path))[0]
        print(f"\\n[{{idx+1}}/{{len(scene_files)}}] Processing Scene: {{scene_name}}")

        try:
            scene_data = compress_json.load(scene_path)
            # Let CameraSkills create the house, calculate bounds, and deduplicate boxes.
            success = skills.load_scene(scene_name, scene_data)
            if success:
                # Hand control to the agent-generated trajectory logic.
                trajectory_worker.execute(scene_name, args.output_dir)
        except Exception as e:
            print(f"!!! Error processing {{scene_name}}: {{e}}")
            import traceback
            traceback.print_exc()

    controller.stop()
    print("\\n[All Done] Data Collection Completed!")
"""
    return thor_runner_template

def main():
    parser = ArgumentParser(description="AI2-THOR Camera Agent Orchestrator")
    parser.add_argument(
        "--task_keys",
        type=str,
        default="all",
        help="Comma-separated task keys. Use 'all' to run every task in Instructions.py.",
    )
    parser.add_argument(
        "--scenes_root",
        type=str,
        default=DEFAULT_SCENES_ROOT,
        help="Directory containing Holodeck-compatible scene JSON files.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for captured images and metadata JSON files.",
    )
    args = parser.parse_args()
    args.scenes_root = os.path.abspath(args.scenes_root)
    args.output_dir = os.path.abspath(args.output_dir)

    if args.task_keys.lower() == "all":
        # Read all task names directly from CameraInstructions.TASKS.
        if hasattr(CameraInstructions, "TASKS"):
            task_keys_to_run = list(CameraInstructions.TASKS.keys())
            print(f"🔄 Detected 'all' mode; loaded {len(task_keys_to_run)} tasks: {task_keys_to_run}")
        else:
            print("❌ CameraInstructions.TASKS was not found. Check Instructions.py.")
            return
    else:
        task_keys_to_run = [k.strip() for k in args.task_keys.split(",") if k.strip()]

    if not task_keys_to_run:
        print("❌ No valid tasks were found. Exiting.")
        return

    # ===================================================================
    # Phase 0: Load the model once
    # ===================================================================
    try:
        llm = TextGenerationBackend(MODEL_PATH, max_model_len=8192)
        print(f"=== {llm.backend} backend loaded successfully ===")
    except Exception as e:
        print(f"[Error] Model load failed: {e}")
        raise SystemExit(1)

    generation_config = GenerationConfig(temperature=0.0, max_tokens=4096)
    generated_scripts = []

    # ===================================================================
    # Phases 1 and 2: Generate code for every task
    # ===================================================================
    for t_key in task_keys_to_run:
        print(f"\n" + "="*60)
        print(f"🚀 Processing Generation for Task: [{t_key}]")
        print("="*60)

        try:
            user_instruction = CameraInstructions.get_instruction(t_key)
        except KeyError:
            print(f"⚠️ Task key not found: {t_key}. Skipped.")
            continue

        print("\n[Phase 1] 🧠 Architect Agent is analyzing the instruction...")
        arch_sys = CameraArchitectPrompts.get_system_prompt()
        arch_user = CameraArchitectPrompts.get_user_prompt(user_instruction)
        arch_msg = [{"role": "system", "content": arch_sys}, {"role": "user", "content": arch_user}]
        arch_output = llm.generate_messages(arch_msg, generation_config)

        task_meta_list = extract_json_from_text(arch_output)
        if not task_meta_list:
            print(f"❌ The Architect did not produce valid JSON. Skipping task [{t_key}].")
            continue

        task_meta = task_meta_list[0]
        print(f"✅ Task Meta Extracted: {task_meta['task_name']}")
        print(json.dumps(task_meta, indent=2, ensure_ascii=False))
        print("\n[Phase 2] 💻 Coder Agent is writing the trajectory logic...")
        coder_sys = CameraCoderPrompts.get_system_prompt()
        coder_user = CameraCoderPrompts.get_user_prompt(task_meta, t_key)
        coder_msg = [{"role": "system", "content": coder_sys}, {"role": "user", "content": coder_user}]
        coder_output = llm.generate_messages(coder_msg, generation_config)

        generated_class_code = extract_python_from_text(coder_output)
        class_name = f"{task_meta['task_name'].title().replace('_', '')}Trajectory"

        final_script_content = build_runner_script(generated_class_code, class_name, task_meta)

        code_save_dir = os.path.join(PIPELINE_DIR, "gen_code", t_key)
        os.makedirs(code_save_dir, exist_ok=True)
        script_filename = os.path.join(code_save_dir, f"gen_{task_meta['task_name']}.py")

        with open(script_filename, "w", encoding="utf-8") as f:
            f.write(final_script_content)

        print(f"✅ Script generated and saved for [{t_key}]: {script_filename}")
        generated_scripts.append((t_key, script_filename))

    # ===================================================================
    # Phase 3: Release model memory before execution
    # ===================================================================
    print("\n[Phase 3] 🧹 Generation complete. Releasing model memory for AI2-THOR...")
    llm.close()
    del llm
    gc.collect()

    if not generated_scripts:
        print("\n❌ No scripts were generated successfully. Exiting.")
        return

    # ===================================================================
    # Phase 4: Execute all generated collection tasks
    # ===================================================================
    print("\n" + "#"*60)
    print("🎬 STARTING BATCH EXECUTION")
    print("#"*60)

    for t_key, script_filename in generated_scripts:
        print(f"\n▶️ Executing Task: [{t_key}] -> Script: {script_filename}")

        try:
            cmd = [
                "python", script_filename,
                "--scenes_root", args.scenes_root,
                "--output_dir", args.output_dir
            ]

            env = os.environ.copy()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, ".."))
            env["PYTHONPATH"] = f"{project_root}{os.pathsep}{current_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

            subprocess.run(cmd, check=True, env=env)
            print(f"✅ Execution for [{t_key}] finished successfully.")

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Execution Failed for [{t_key}]. Skipping to next task...")
        except KeyboardInterrupt:
            print("\n⏹️ User manually interrupted. Aborting remaining tasks.")
            break

    print("\n🎉 ALL TASKS COMPLETED!")

if __name__ == "__main__":
    main()
