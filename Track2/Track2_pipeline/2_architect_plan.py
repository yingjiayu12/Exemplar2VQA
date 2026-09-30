import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0,1")
os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
import json
import re
from Prompt import ArchitectPrompts
from Example import QA_FEW_SHOT

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPOSITORY_ROOT = os.path.abspath(os.path.join(AGENT_DIR, "..", ".."))
if REPOSITORY_ROOT not in os.sys.path:
    os.sys.path.append(REPOSITORY_ROOT)
from shared.llm_backend import GenerationConfig, TextGenerationBackend

SCENE_ID = os.environ.get("EXEMPLAR2VQA_SCENE_ID", "scene_0")
DATA_ROOT = os.path.abspath(
    os.environ.get("EXEMPLAR2VQA_DATA_ROOT", os.path.join(AGENT_DIR, "data"))
)
BASE_DIR = os.path.join(DATA_ROOT, SCENE_ID)
MODEL_PATH = os.environ.get("EXEMPLAR2VQA_MODEL_PATH", "Qwen/Qwen3-Coder-30B-A3B-Instruct")

def load_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def clean_json_response(response_text):
    if not response_text: return []
    match = re.search(r'```json\s*(.*?)```', response_text, re.DOTALL)
    if match:
        content = match.group(1).strip()
    else:
        start_list = response_text.find('[')
        start_dict = response_text.find('{')
        if start_list != -1 and (start_dict == -1 or start_list < start_dict):
            end = response_text.rfind(']')
            content = response_text[start_list:end+1]
        elif start_dict != -1:
            end = response_text.rfind('}')
            content = response_text[start_dict:end+1]
        else:
            content = response_text.strip()
            
    return content

def main():
    print(f"=== Step 1: Architect Planning for {SCENE_ID} ===")
    if not os.path.exists(BASE_DIR):
        print(f"[Info] Creating directory: {BASE_DIR}")
        os.makedirs(BASE_DIR, exist_ok=True)

    try:
        llm = TextGenerationBackend(MODEL_PATH, max_model_len=16384)
        print(f"=== {llm.backend} backend loaded successfully ===")
    except Exception as e:
        print(f"[Error] Model load failed: {e}")
        raise SystemExit(1)

    # ---------------- Prepare data and prompts ----------------
    bbox_schema_path = os.path.join(BASE_DIR, f"schema_{SCENE_ID}_bbox.json")
    view_schema_path = os.path.join(BASE_DIR, f"schema_{SCENE_ID}_visible_views.json")
    if not os.path.exists(bbox_schema_path):
        print(f"[Warning] Schema not found at: {bbox_schema_path}. Using dummy schema for prompt generation.")
        bbox_schema_str = '[{"id": "0_1", "category": "chair", "min": [0,0,0], "max": [1,1,1]}]'
    else:
        bbox_schema_str = load_file(bbox_schema_path)

    if not os.path.exists(view_schema_path):
        view_schema_str = '{"views": {"0": {"visible_objects": [{"id": "0_1"}]}}}'
    else:
        view_schema_str = load_file(view_schema_path)
    
    sys_msg = ArchitectPrompts.get_system_prompt()
    user_msg = ArchitectPrompts.get_user_prompt(
        qa_examples_str=QA_FEW_SHOT, 
        bbox_schema_str=bbox_schema_str, 
        view_schema_str=view_schema_str
    )
    
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg}
    ]
    
    print(">>> Architect Agent is analyzing the examples from Example.py...")

    llm_response = llm.generate_messages(
        messages,
        GenerationConfig(temperature=0.7, top_p=0.9, max_tokens=2048),
    )
    try:
        cleaned_json = clean_json_response(llm_response)
        parsed_data = json.loads(cleaned_json)
        if isinstance(parsed_data, dict):
            if "tasks" in parsed_data:
                tasks = parsed_data["tasks"]
            else:
                tasks = next((v for v in parsed_data.values() if isinstance(v, list)), [])
        elif isinstance(parsed_data, list):
            tasks = parsed_data
        else:
            tasks = []

        if not tasks:
            print("[Error] Parsed JSON is not a list or valid dict format.")
            print("Raw:", cleaned_json)
            return

        output_path = os.path.join(BASE_DIR, "tasks.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)
            
        print(f"\n[Success] Generated {len(tasks)} tasks.")
        print(f"Saved to: {output_path}")
        
        print("\n" + "="*20 + " TASK PREVIEW " + "="*20)
        for i, t in enumerate(tasks):
            t_name = t.get('task_name', 'MISSING_NAME')
            t_tpl = t.get('question_template', 'MISSING_TEMPLATE')
            print(f"[{i+1}] Task: {t_name}")
            print(f"    Template : {t_tpl}")
            print(f"    Params   : {t.get('parameters', [])}")
            print("-" * 50)
            
    except json.JSONDecodeError as e:
        print(f"[Error] JSON Parse Failed: {e}")
        print("Raw Output Snippet:", llm_response[:500])

if __name__ == "__main__":
    main()