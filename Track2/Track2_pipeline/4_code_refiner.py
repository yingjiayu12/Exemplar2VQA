import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0,1")
os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
import json
import re
import sys
import logging
import subprocess
from Prompt import ReviewerPrompts, RefinerPrompts
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
TRACK2_ROOT = os.path.abspath(os.path.join(AGENT_DIR, ".."))
REPOSITORY_ROOT = os.path.abspath(os.path.join(TRACK2_ROOT, ".."))
SCENE_ID = os.environ.get("EXEMPLAR2VQA_SCENE_ID", "scene_0")
DATA_ROOT = os.path.abspath(
    os.environ.get("EXEMPLAR2VQA_DATA_ROOT", os.path.join(AGENT_DIR, "data"))
)
MODEL_PATH = os.environ.get("EXEMPLAR2VQA_MODEL_PATH", "Qwen/Qwen3-Coder-30B-A3B-Instruct")

for import_path in (AGENT_DIR, TRACK2_ROOT, REPOSITORY_ROOT):
    if import_path not in sys.path:
        sys.path.append(import_path)
from shared.llm_backend import GenerationConfig, TextGenerationBackend

class CodeRefinerAgent:
    def __init__(self):
        try:
            self.llm = TextGenerationBackend(MODEL_PATH, max_model_len=8192)
            print(f"=== {self.llm.backend} backend ready ===")
        except Exception as e:
            print(f"Error: {e}")
            raise SystemExit(1)

    def _call_llm(self, sys_msg, user_msg, max_tokens=2048):
        messages = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]
        return self.llm.generate_messages(
            messages,
            GenerationConfig(temperature=0.1, top_p=0.95, max_tokens=max_tokens),
        )

    def run_review(self, task, code):
        """Review Stage"""
        print(f"   [Review] Analyzing...")
        deterministic_issues = []
        if "[YOUR CODE HERE]" in code:
            deterministic_issues.append("The generated script still contains a placeholder.")
        try:
            compile(code, "<generated_qa>", "exec")
        except SyntaxError as exc:
            deterministic_issues.append(f"Python syntax error: {exc}")

        sys_msg = ReviewerPrompts.get_system_prompt()
        user_msg = ReviewerPrompts.get_user_prompt(task, code)
        raw = self._call_llm(sys_msg, user_msg, max_tokens=512)
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            review = json.loads(match.group(0)) if match else {}
        except (json.JSONDecodeError, TypeError):
            review = {}

        if deterministic_issues:
            review["score"] = 0
            review["pass"] = False
            review["critical_issues"] = deterministic_issues + review.get(
                "critical_issues", []
            )
        return review or {
            "score": 0,
            "pass": False,
            "critical_issues": ["JSON parse error"],
        }

    def run_refine(self, task, original_code, review):
        """Refine Stage"""
        print(f"   [Refine] Fixing issues...")
        sys_msg = RefinerPrompts.get_system_prompt()
        user_msg = RefinerPrompts.get_user_prompt(task, original_code, review)
        raw = self._call_llm(sys_msg, user_msg, max_tokens=4096)
        match = re.search(r'```python\s*(.*?)```', raw, re.DOTALL)
        code = match.group(1).strip() if match else raw.strip()

        if "import os" not in code:
            code = "import os\nimport json\nimport logging\nimport math\nimport numpy as np\nfrom collections import Counter\n" + code
        return code

    def run_test(self, task_name, script_path):
        """Execution Stage"""
        print(f"   [Test] Running {os.path.basename(script_path)}...")
        cmd = ['python', script_path, '--processed_data_path', DATA_ROOT, '--dataset', 'holodeck', '--output_dir', os.path.join(DATA_ROOT, SCENE_ID), '--num_workers', '1']
        env = os.environ.copy()
        env["PYTHONPATH"] = (
            f"{TRACK2_ROOT}{os.pathsep}{AGENT_DIR}{os.pathsep}"
            f"{env.get('PYTHONPATH', '')}"
        )

        try:
            res = subprocess.run(cmd, cwd=os.path.join(DATA_ROOT, SCENE_ID), capture_output=True, text=True, env=env)
            if res.returncode != 0:
                print(f"      ❌ Runtime Error: {res.stderr.strip().splitlines()[-1] if res.stderr else 'Unknown'}")
                return False, 0

            json_path = os.path.join(DATA_ROOT, SCENE_ID, f"qa_{task_name}_holodeck.json")
            if os.path.exists(json_path):
                with open(json_path) as f: data = json.load(f)
                count = len(data)
                print(f"      ✅ Generated {count} items.")
                return True, count
            return False, 0
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            return False, 0

    def process_scene(self):
        tasks_path = os.path.join(DATA_ROOT, SCENE_ID, "tasks.json")
        if not os.path.exists(tasks_path): return

        with open(tasks_path, 'r') as f: tasks = json.load(f)

        for task in tasks:
            task_name = task['task_name']
            orig_script = os.path.join(DATA_ROOT, SCENE_ID, f"gen_{task_name}.py")

            if not os.path.exists(orig_script): continue

            print(f"\n{'='*40}\n>>> Task: {task_name}\n{'='*40}")
            with open(orig_script, 'r') as f: current_code = f.read()

            MAX_CYCLES = 2
            best_code = None

            for i in range(MAX_CYCLES):
                ver = i + 1
                print(f"\n--- Cycle {ver} ---")

                # 1. Review
                review = self.run_review(task, current_code)
                score = review.get("score", 0)
                passed = review.get("pass", False)
                issues = review.get("critical_issues", [])

                print(f"   [Report] Score: {score}/100 | Pass: {passed}")
                if issues: print(f"   [Issues] {json.dumps(issues, indent=2)}")

                # 2. Refine
                if not passed or score < 90:
                    current_code = self.run_refine(task, current_code, review)

                    # 3. Save Version
                    v_name = f"gen_{task_name}_v{ver}.py"
                    v_path = os.path.join(DATA_ROOT, SCENE_ID, v_name)
                    with open(v_path, 'w') as f: f.write(current_code)
                    print(f"   💾 Saved: {v_name}")

                    # 4. Test Run
                    ok, count = self.run_test(task_name, v_path)

                    if ok and count > 0 and passed:
                        print("   🏆 Perfect Candidate Found!")
                        best_code = current_code
                        break
                else:
                    print("   ✨ Code is already good.")
                    break

            # End of loop
            print("\n--- Done ---")

def main():
    agent = CodeRefinerAgent()
    agent.process_scene()

if __name__ == "__main__":
    main()
