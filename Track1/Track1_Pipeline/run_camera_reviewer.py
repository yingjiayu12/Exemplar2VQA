import os
import sys
import json
import re
import subprocess
import shutil
from argparse import ArgumentParser

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0,1")
os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")

from Prompt import CameraArchitectPrompts, CameraReviewerPrompts, CameraRefinerPrompts
from Instructions import CameraInstructions

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
REPOSITORY_ROOT = os.path.abspath(os.path.join(PIPELINE_DIR, "..", ".."))
if REPOSITORY_ROOT not in sys.path:
    sys.path.append(REPOSITORY_ROOT)
from shared.llm_backend import GenerationConfig, TextGenerationBackend

DEFAULT_SCENES_ROOT = os.path.abspath(os.path.join(PIPELINE_DIR, "..", "data", "scenes"))
DEFAULT_OUTPUT_DIR = os.path.abspath(os.path.join(PIPELINE_DIR, "..", "data", "collected"))
MODEL_PATH = os.environ.get("EXEMPLAR2VQA_MODEL_PATH", "Qwen/Qwen3-Coder-30B-A3B-Instruct")
MAX_RETRIES = 6  # Maximum number of closed-loop revisions (V1 through V6).

def extract_json_from_text(text):
    try:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match: return json.loads(match.group(1))
        list_match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
        if list_match: return json.loads(list_match.group(0))
        dict_match = re.search(r'\{.*\}', text, re.DOTALL)
        if dict_match: return json.loads(dict_match.group(0))
    except Exception as e:
        print(f"[JSON Parse Error] {e}")
    return None

def extract_python_from_text(text):
    match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

def clean_unity_logs(raw_log):
    cleaned_lines = []
    spam_keywords = [
        "Fallback handler", "Initialize engine", "Display 0", "Desktop is", 
        "CrashReporter", "Compositor", "Vulkan", "OpenGL", "ALSA", "AudioManager", 
        "Loaded scene", "Resolving", "Unloading", "The referenced script", 
        "PlayerConnection", "GfxDevice", "xrandr", "libudev"
    ]
    for line in raw_log.split('\n'):
        line_stripped = line.strip()
        if not line_stripped or any(spam in line for spam in spam_keywords):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def smart_truncate_logs(logs, max_chars=4000):
    if len(logs) <= max_chars:
        return logs
    head = logs[:500]
    tail = logs[-(max_chars - 500):]
    return f"{head}\n\n... [LOG TOO LONG: TRUNCATED {len(logs)-max_chars} CHARS] ...\n\n{tail}"

def run_with_llm_inference(llm, generation_config, system_prompt, user_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return llm.generate_messages(messages, generation_config)

def main():
    parser = ArgumentParser()
    parser.add_argument("--task_keys", type=str, default="all")
    parser.add_argument("--scenes_root", type=str, default=DEFAULT_SCENES_ROOT)
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.scenes_root = os.path.abspath(args.scenes_root)
    args.output_dir = os.path.abspath(args.output_dir)

    if args.task_keys.lower() == "all":
        if hasattr(CameraInstructions, "TASKS"):
            task_keys_to_run = list(CameraInstructions.TASKS.keys())
            print(f"🔄 Detected 'all' mode; loaded tasks: {task_keys_to_run}")
        else:
            print("❌ CameraInstructions.TASKS was not found.")
            return
    else:
        task_keys_to_run = [k.strip() for k in args.task_keys.split(",") if k.strip()]

    try:
        llm = TextGenerationBackend(MODEL_PATH, max_model_len=8192)
        print(f"=== {llm.backend} backend loaded successfully ===")
    except Exception as e:
        print(f"[Error] Model load failed: {e}")
        raise SystemExit(1)
    generation_config = GenerationConfig(temperature=0.0, max_tokens=8192)

    for t_key in task_keys_to_run:
        print(f"\n" + "="*60 + f"\n🚀 Task: [{t_key}]\n" + "="*60)
        
        try:
            user_instruction = CameraInstructions.get_instruction(t_key)
        except KeyError:
            continue

        arch_out = run_with_llm_inference(llm, generation_config, CameraArchitectPrompts.get_system_prompt(), CameraArchitectPrompts.get_user_prompt(user_instruction))
        task_meta = extract_json_from_text(arch_out)
        
        if not task_meta:
            continue
        if isinstance(task_meta, list):
            task_meta = task_meta[0]
        
        code_dir = os.path.join(PIPELINE_DIR, "gen_code", t_key)
        base_script_name = f"gen_{task_meta.get('task_name', 'task')}.py"
        current_script_path = os.path.join(code_dir, base_script_name)
        
        if not os.path.exists(current_script_path):
            continue

        with open(current_script_path, "r", encoding="utf-8") as f: 
            current_code = f.read()

        env_log_path = os.path.join(code_dir, "env_feedback.log")

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n🔄 [Attempt {attempt}/{MAX_RETRIES}] Executing Code V{attempt}...")
            
            if os.path.exists(env_log_path):
                os.remove(env_log_path)

            tmp_sandbox_dir = os.path.join(code_dir, f"tmp_data_output_v{attempt}")
            if os.path.exists(tmp_sandbox_dir):
                shutil.rmtree(tmp_sandbox_dir)
            os.makedirs(tmp_sandbox_dir, exist_ok=True)

            cmd = ["python", current_script_path, "--scenes_root", args.scenes_root, "--output_dir", tmp_sandbox_dir]
            env = os.environ.copy()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            env["PYTHONPATH"] = f"{os.path.abspath(os.path.join(current_dir, '..'))}{os.pathsep}{current_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
                raw_logs = result.stdout + "\n" + result.stderr
            except subprocess.TimeoutExpired as e:
                raw_logs = f"[Timeout Error] Script execution exceeded 600 seconds.\n{e.stdout}\n{e.stderr}"

            env_feedback = ""
            if os.path.exists(env_log_path):
                with open(env_log_path, "r", encoding="utf-8") as f:
                    env_feedback = f.read()

            clean_console_logs = clean_unity_logs(raw_logs)
            combined_logs = f"=== CONSOLE LOGS (Python Errors) ===\n{clean_console_logs}\n\n=== ENV FEEDBACK LOGS (Physics Collisions) ===\n{env_feedback}"
            llm_ready_logs = smart_truncate_logs(combined_logs, max_chars=4000)

            debug_log_path = os.path.join(code_dir, f"{base_script_name.replace('.py', '')}_v{attempt}.log")
            with open(debug_log_path, "w", encoding="utf-8") as f: f.write(combined_logs)

            print("🕵️ Reviewer Agent is analyzing execution results...")
            reviewer_out = run_with_llm_inference(
                llm, generation_config,
                CameraReviewerPrompts.get_system_prompt(),
                CameraReviewerPrompts.get_user_prompt(task_meta, current_code, llm_ready_logs)
            )
            
            review_json = extract_json_from_text(reviewer_out) or {"score": 0, "status": "FAIL", "error_summary": "Parse Error"}
            
            print(f"📊 Score: {review_json.get('score')}/100 | Status: {review_json.get('status').upper()} | Category: {review_json.get('error_category')}")
            print(f"📝 Feedback: {review_json.get('error_summary')}")

            if review_json.get("score", 0) >= 90 or str(review_json.get("status")).lower() == "pass":
                print(f"✅ Success! Code V{attempt} runs without logic or physics errors.")
                shutil.copytree(tmp_sandbox_dir, args.output_dir, dirs_exist_ok=True)
                print(f"📁 Successful output was copied to: {args.output_dir}")
                break
                
            if os.path.exists(tmp_sandbox_dir):
                shutil.rmtree(tmp_sandbox_dir)
                print(f"🗑️ The failed attempt output was removed: {tmp_sandbox_dir}")

            if attempt == MAX_RETRIES:
                print(f"❌ Max retries reached. Could not resolve all errors.")
                break
                
            print("🔧 Refiner Agent is rewriting code based on feedback...")
            refiner_out = run_with_llm_inference(
                llm, generation_config,
                CameraRefinerPrompts.get_system_prompt(),
                CameraRefinerPrompts.get_user_prompt(current_code, review_json)
            )
            current_code = extract_python_from_text(refiner_out)
            
            current_script_path = os.path.join(code_dir, f"{base_script_name.replace('.py', '')}_v{attempt + 1}.py")
            with open(current_script_path, "w", encoding="utf-8") as f: f.write(current_code)

if __name__ == "__main__":
    main()