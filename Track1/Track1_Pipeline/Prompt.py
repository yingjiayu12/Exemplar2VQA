import textwrap
import json

from camera_skills_reference import CAMERA_SKILLS_INTERFACE_STR

class CameraArchitectPrompts:
    @staticmethod
    def get_system_prompt():
        return textwrap.dedent("""
            # Role
            You are an Expert Embodied AI Data Architect specializing in 3D scene data collection (like AI2-THOR/Holodeck).

            # Context
            We need to generate tasks that instruct a Camera Coder to extract TWO specific types of JSON files per target/scene.

            # Workflow
            1. **Analyze**: Read the user's natural language instruction.
            2. **Extract Parameters**: Identify targets, angles, radius logic, and ANY early stopping constraints (e.g., "stop after 2 objects").
            3. **Generalize**: Output the task definition.

            # Output Format (STRICT JSON)
            Return a strictly valid JSON LIST. Use EXACTLY these keys. DO NOT wrap the list in a dictionary.
            
            [
                {
                    "task_name": "name_of_task_snake_case",
                    "description": "Brief description of the camera trajectory.",
                    "target_filters": {
                        "whitelist": ["bed", "sofa"], 
                        "blacklist": ["wall", "floor", "ceiling", "window", "room", "structure"]
                    },
                    "trajectory": {
                        "type": "orbit", // or "room_center"
                        "angles": [0, 90, 180, 270], 
                        "base_radius": 1.5, 
                        "adaptive_radius_logic": "base_radius + obj['max_dim'] / 2.0", 
                        "camera_height": 1.65, 
                        "camera_pitch": -15.0 
                    },
                    "constraints": {
                        "require_all_angles_success": true, 
                        "min_visible_pixels": 300,
                        "max_targets": 2 // INT or null. ONLY add if user specifies stopping after N objects.
                    },
                    "output_format": {
                        "save_global_bbox": true,
                        "views_json_suffix": "views"
                    },
                    "save_dir_name": "orbit_views"
                }
            ]
        """).strip()

    @staticmethod
    def get_user_prompt(user_instruction_str):
        return textwrap.dedent(f"""
            # User Camera Instruction
            ```text
            {user_instruction_str}
            ```
            # Task
            Analyze the instruction above. 
            Ensure `output_format` indicates saving a global bbox and specify the views suffix.
            Return ONLY the JSON list.
        """).strip()
    
class CameraCoderPrompts:
    @staticmethod
    def get_system_prompt():
        return textwrap.dedent("""
            # Role
            You are an Expert Python Developer for Embodied AI data collection.
            Your job is to generate executable Python code that controls a simulator camera and saves exactly formatted JSON datasets.

            # CRITICAL RULES (MUST FOLLOW)
            1. **Holodeck Duplication Fix**: Holodeck often spawns multiple objects at the same position. `CameraSkills` already fixes this. You will get clean IDs like `meeting_chair-5`.
            2. **Global BBox JSON**: If `output_format.save_global_bbox` is true, you MUST fetch `skills.get_scene_metadata()` and save it once per scene as `<scene_name>_bbox` using `skills.save_json()`.
            3. **Aggregated Views JSON**: Do NOT save a JSON file for every single image. You MUST aggregate the views into a single dictionary per target/room and save it as ONE `<id_or_scene>_visible_views` file. DO NOT put raw environment feedback inside this views dictionary.
            4. **Image & File Naming Convention**: 
               - For images: Use `f"{scene_name}_room_view_{angle}"` (for room_center) or `f"{target_id}_view_{angle}"` (for orbit). 
               - Append `.png` when saving the `image_path` string into the JSON dict.
            5. **NO HALLUCINATIONS**: Do NOT use `self.skills.task_meta`. Hardcode the parameters as local variables inside your `execute` method based on the provided JSON.
            6. **TWO-PASS EXECUTION & TEXT LOGGING**: 
               - **Phase 1 (Trial)**: Use `dry_run=True`. You MUST write feedback to a `.log` text file located in the same directory as the script. If `result['success']` is False, explicitly log the `error_message` and the agent's position from `raw_metadata`. If True, log a simple success message.
               - **Phase 2 (Record)**: Run `dry_run=False` ONLY on valid coordinates. Save ONLY clean vision data to the views JSON.

            # Output Format
            Return ONLY the Full Python Script inside standard markdown ```python ... ``` blocks.
        """).strip()

    @staticmethod
    def get_user_prompt(task_meta, task_key):
        class_name = f"{task_meta['task_name'].title().replace('_', '')}Trajectory"
        task_meta_str = json.dumps(task_meta, indent=2)
        
        return textwrap.dedent(f"""
            # Task Meta Config
            ```json
            {task_meta_str}
            ```

            # SKELETON (STRICT ENFORCEMENT)
            Complete the logic below. Implement the dual-JSON saving logic, the Two-Pass logic, and the TXT Logging logic to the script's directory.
            
            ```python
            import os
            from datetime import datetime

            class {class_name}:
                def __init__(self, skills):
                    self.skills = skills

                def execute(self, scene_name, base_output_dir):
                    print(f"\\n>>> Starting Task: {task_meta['task_name']} on scene: {{scene_name}}")
                    
                    # Setup output directory for images/json
                    save_dir = os.path.join(base_output_dir, scene_name, "{task_key}")
                    os.makedirs(save_dir, exist_ok=True)
                    
                    # Setup Logging in the SCRIPT's directory (e.g., gen_code/A/), NOT the image output dir
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    log_file = os.path.join(script_dir, "env_feedback.log")
                    
                    def write_log(msg):
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(f"[{{datetime.now().strftime('%H:%M:%S')}}] {{msg}}\\n")
                    
                    write_log(f"--- Processing Scene: {{scene_name}} ---")

                    # --- STEP 1: LOGIC IMPLEMENTATION ---
                    # 1. Fetch metadata and save: `self.skills.save_json(metadata_dict, save_dir, f"{{scene_name}}_bbox")`
                    
                    # 2. HARDCODE variables (Read directly from JSON):
                    #    trajectory_type = "..." (read from JSON)
                    #    angles = [...]
                    #    camera_height = ...
                    #    camera_pitch = abs(...) 
                    #    base_radius = ...
                    #    max_targets = ...
                    #    whitelist = [...]
                    #    blacklist = [...]
                    
                    # 3. Trajectory Logic:
                    # ==========================================
                    # Branch A: ROOM CENTER (Panorama)
                    # ==========================================
                    # if trajectory_type == "room_center":
                    #    a. Get exact coords: `cx, cz = self.skills.get_room_info()['center'][0], self.skills.get_room_info()['center'][2]`
                    #    b. PHASE 1 (TRIAL & TEXT LOGGING): 
                    #       - valid_angles = []
                    #       - For each `angle` in `angles`:
                    #           - result = self.skills.capture_and_parse(x=cx, y=camera_height, z=cz, yaw=angle, pitch=camera_pitch, dry_run=True)
                    #           - if result["success"]: 
                    #               - write_log(f"Angle {{angle}} -> SUCCESS")
                    #               - valid_angles.append(angle)
                    #           - else:
                    #               - err = result.get('error_message', 'Unknown Error')
                    #               - pos_info = result.get('raw_metadata', {{}}).get('agent', {{}}).get('position', {{}})
                    #               - write_log(f"Angle {{angle}} -> ERROR: {{err}} | Blocked at pos: {{pos_info}}")
                    #    c. PHASE 2 (RECORD CLEAN DATA): 
                    #       - Initialize clean dict: `vqa_data_dict = {{"position": {{"x": cx, "y": camera_height, "z": cz}}, "views": {{}}}}`
                    #       - Loop through `angle` in `valid_angles`:
                    #           - result = self.skills.capture_and_parse(x=cx, y=camera_height, z=cz, yaw=angle, pitch=camera_pitch, dry_run=False)
                    #           - if not result["success"]: continue
                    #           - img_name = f"{{scene_name}}_room_view_{{angle}}"
                    #           - self.skills.save_image(result["rgb_frame"], save_dir, img_name)
                    #           - vqa_data_dict["views"][str(angle)] = {{"image_path": f"{{img_name}}.png", "position": result["position"], "rotation": result["rotation"], "visible_objects": result["visible_objects"]}}
                    #    d. Save aggregated JSON: `self.skills.save_json(vqa_data_dict, save_dir, f"{{scene_name}}_visible_views")`
                    
                    # ==========================================
                    # Branch B: ORBIT (Around Object)
                    # ==========================================
                    # elif trajectory_type == "orbit":
                    #    a. Get targets EXACTLY like this:
                    #       targets = self.skills.get_object_list(category_whitelist=whitelist if whitelist else None, category_blacklist=blacklist if blacklist else None)
                    #    b. Set counter: `successful_count = 0`
                    #    c. Loop through `obj` in `targets`:
                    #       d. Get exact coords: `cx, cz = obj['centroid'][0], obj['centroid'][2]`
                    #       e. CALL API EXACTLY: `orbit_positions = self.skills.calculate_orbit_positions(cx, cz, base_radius + obj['max_dim'] / 2.0, angles)`
                    #       f. PHASE 1 (TRIAL & TEXT LOGGING):
                    #          - valid_positions = []
                    #          - For each `pos` in `orbit_positions`:
                    #              - result = self.skills.capture_and_parse(x=pos["x"], y=camera_height, z=pos["z"], yaw=pos["yaw"], pitch=camera_pitch, dry_run=True)
                    #              - if result["success"]:
                    #                  - write_log(f"Target {{obj['id']}} Angle {{pos['yaw']}} -> SUCCESS")
                    #                  - valid_positions.append(pos)
                    #              - else:
                    #                  - err = result.get('error_message', 'Unknown Error')
                    #                  - pos_info = result.get('raw_metadata', {{}}).get('agent', {{}}).get('position', {{}})
                    #                  - write_log(f"Target {{obj['id']}} Angle {{pos['yaw']}} -> ERROR: {{err}} | Agent Pos: {{pos_info}}")
                    #       g. CONSTRAINT CHECK: 
                    #          if require_all_angles_success and len(valid_positions) < len(angles): 
                    #              write_log(f"Target {{obj['id']}} skipped due to angle constraint.\\n")
                    #              continue
                    #       h. PHASE 2 (RECORD CLEAN DATA): 
                    #          - Initialize clean dict: `vqa_data_dict = {{"position": {{"x": cx, "y": camera_height, "z": cz}}, "views": {{}}}}`
                    #          - For each `pos` in `valid_positions`:
                    #              - result = self.skills.capture_and_parse(x=pos["x"], y=camera_height, z=pos["z"], yaw=pos["yaw"], pitch=camera_pitch, dry_run=False)
                    #              - if not result["success"]: continue
                    #              - img_name = f"{{obj['id']}}_view_{{pos['yaw']}}"
                    #              - self.skills.save_image(result["rgb_frame"], save_dir, img_name)
                    #              - vqa_data_dict["views"][str(pos["yaw"])] = {{"image_path": f"{{img_name}}.png", "position": result["position"], "rotation": result["rotation"], "visible_objects": result["visible_objects"]}}
                    #       i. Save `vqa_data_dict` named `f"{{obj['id']}}_visible_views"` using self.skills.save_json().
                    #       j. write_log(f"Target {{obj['id']}} fully completed.\\n")
                    #       k. Increment counter: `successful_count += 1`
                    #       l. EARLY STOPPING: If `max_targets` is not None and `successful_count >= max_targets`, break.
                    
                    print(f"    [Done] Task {task_meta['task_name']} completed.")
            ```
            
            Return the Full, completed Python code now.
        """).strip()
    
class CameraReviewerPrompts:
    @staticmethod
    def get_system_prompt():
        return textwrap.dedent("""
            # Role
            You are an Expert Code Reviewer and Embodied AI Diagnostics Specialist for AI2-THOR.

            # Objective
            Analyze the provided Python code and the combined execution logs. 
            Determine the exact reason for failure. 

            # CRITICAL BUSINESS LOGIC (READ CAREFULLY)
            In Embodied AI data collection, it is **COMPLETELY NORMAL AND EXPECTED** for the agent to hit walls ("Collision") during Phase 1 (Trial). The code is designed to test angles and **SKIP** objects if they are blocked by walls or bounds. 
            - DO NOT penalize the code if you see objects being skipped or logs showing "ERROR: Collision". This means the filter is working perfectly!
            - ONLY penalize physical errors if the logs indicate that **ZERO objects were successfully collected** because a hardcoded parameter (like `base_radius=1.5` or `camera_height`) is completely impossible for the entire scene.

            # Scoring System (0-100)
            - 90-100: Flawless execution. No Python crashes. Skipping objects due to constraints is perfectly fine and counts as a SUCCESS, as long as the script finishes gracefully.
            - 70-89: Pass with minor code inefficiency, but data was collected.
            - 40-69: Fail - Fatal Physics Error. The parameters (e.g., base_radius, camera_height) are so extreme that the agent failed on EVERY SINGLE OBJECT and collected nothing. The Refiner must tune the numbers.
            - 0-39: Fail - Fatal Logic/Code Error. Python syntax errors, Tracebacks, wrong dictionary keys (e.g., `KeyError`), missing rules.

            # Output Format (STRICT JSON)
            Return ONLY a valid JSON object.
            {
                "score": 85,
                "status": "pass" | "fail",
                "error_category": "none" | "python_syntax" | "physics_environment" | "logic_mismatch",
                "error_summary": "Brief explanation. (e.g., 'Script worked perfectly, skipped invalid objects as expected.')",
                "refiner_instructions": "Direct instructions to fix the code. If pass, leave empty. If all objects failed, suggest changing `base_radius` or `camera_pitch`.",
                "extracted_traceback": "Specific lines of Python error. Leave empty if no Python crash."
            }
        """).strip()

    @staticmethod
    def get_user_prompt(task_meta, generated_code, logs_content):
        return textwrap.dedent(f"""
            # Task Meta
            ```json
            {json.dumps(task_meta, indent=2, ensure_ascii=False)}
            ```

            # Generated Code
            ```python
            {generated_code}
            ```

            # Combined Logs (Console & Env Feedback)
            ```text
            {logs_content}
            ```

            Analyze the execution logs against the generated code. 
            Remember: Skipped objects due to collisions are EXPECTED. Do not fail the code for expected physical constraints unless 0 data was collected.
            Return the assessment in the strict JSON format requested.
        """).strip()

class CameraRefinerPrompts:
    @staticmethod
    def get_system_prompt():
        return textwrap.dedent("""
            # Role
            You are an Expert Python Developer for Embodied AI data collection.
            Your code failed the Reviewer's check. You must fix it.

            # CRITICAL RULES (MUST FOLLOW)
            1. **Fixing Logic Errors**: Correct Python syntax, fix variable names (e.g., use `obj['centroid']`), and ensure proper loop logic.
            2. **Fixing Physics Errors**: If the error is a physics collision or out-of-bounds, YOU MUST TUNE THE NUMBERS. Adjust `camera_pitch`, `camera_height`, or `base_radius` to safely avoid walls/objects.
            3. **NO API HALLUCINATION**: DO NOT invent arguments. Fix the math and logic.
            4. **Preserve Structure**: Keep the dual-JSON saving logic and text Logging logic strictly intact.

            # Output Format
            Return ONLY the Full Python Script inside standard markdown ```python ... ``` blocks.
        """).strip()

    @staticmethod
    def get_user_prompt(original_code, reviewer_feedback):
        return textwrap.dedent(f"""
            # Original Failed Code
            ```python
            {original_code}
            ```

            # Reviewer Feedback
            ```json
            {json.dumps(reviewer_feedback, indent=2, ensure_ascii=False)}
            ```

            Rewrite the Original Code to fix the issues mentioned in the Reviewer Feedback.
            Return ONLY the new Python code.
        """).strip()