import textwrap
import json

UTILS_INTERFACE_STR = textwrap.dedent('''
def get_viewpoint_vectors(angle_deg):
    """
    Calculates the 'Forward' and 'Right' direction vectors for a given viewing angle.
    This establishes the observer's local coordinate system.
    - Forward (+Z relative): The direction the agent is facing.
    - Right (+X relative): The direction to the agent's right.
    Args:
        angle_deg (float): The viewing angle in degrees.
            0 degrees corresponds to Global +Z.
            90 degrees corresponds to Global +X.
    Returns:
        tuple: A tuple containing two numpy arrays (right_vec, fwd_vec).
            - right_vec (np.ndarray): Shape (2,) unit vector pointing Right.
            - fwd_vec (np.ndarray): Shape (2,) unit vector pointing Forward.
    """
    pass

def get_bbox_projection(min_xz, max_xz, axis_vec):
    """
    Projects a 2D Axis-Aligned Bounding Box (AABB) onto a specific 1D axis vector.
    This creates a "shadow" of the object on a line (Separating Axis Theorem concept).
    It is used to determine if objects overlap or are separated along a specific direction
    (e.g., "Is object A entirely to the left of object B?").
    Args:
        min_xz (np.ndarray or list): The [min_x, min_z] coordinates of the object.
        max_xz (np.ndarray or list): The [max_x, max_z] coordinates of the object.
        axis_vec (np.ndarray): A normalized 2D vector representing the projection axis
            (usually the 'Right' or 'Forward' vector from `get_viewpoint_vectors`).
    Returns:
        tuple: (min_proj, max_proj)
            - min_proj (float): The start of the projection interval.
            - max_proj (float): The end of the projection interval.
    """
    pass

def is_spatial_relation_satisfied(direction, ref_projs, target_projs, threshold=0.15):
    """
    Determines if a target object is spatially positioned in a specific direction relative to a reference object.
    It checks strictly non-overlapping conditions. For example, for 'left', the target's
    rightmost edge must be to the left of the reference's leftmost edge (minus a threshold).
    Args:
        direction (str): The direction to check. Must be one of:
            - 'left': Checks if target is to the left of ref (using Right-axis).
            - 'right': Checks if target is to the right of ref (using Right-axis).
            - 'front': Checks if target is in front of ref (using Forward-axis).
            - 'behind': Checks if target is behind ref (using Forward-axis).
        ref_projs (dict): A dict containing projected intervals for the REFERENCE object.
            Must contain keys:
            - 'right_axis': tuple (min, max) projection on the Right vector.
            - 'fwd_axis': tuple (min, max) projection on the Forward vector.
        target_projs (dict): A dict containing projected intervals for the TARGET object.
            Must contain same keys as ref_projs.
        threshold (float): The distance buffer in meters (default 0.15).
            Ensures objects aren't just touching but have a clear gap.
    Returns:
        bool: True if the spatial condition is met, False otherwise.
    """
    pass

def get_object_xz_points(obj_data, include_corners=False):
    """
    Extracts the 2D footprint (X, Z coordinates) of an object from its 3D metadata.
    This tool is essential for converting 3D scene data into 2D planar points for spatial analysis.
    Args:
        obj_data (dict): A dictionary containing the object's 3D geometric properties.
            It MUST contain the following keys:
            - 'centroid': A list or array of 3 floats [x, y, z].
            - 'normalizedAxes': (Required if include_corners=True) A 3x3 rotation matrix.
            - 'axesLengths': (Required if include_corners=True) A list of 3 extents.
        include_corners (bool):
            - If False (default), returns only the centroid (1 point).
            - If True, returns the centroid followed by the 8 corners of the Oriented Bounding Box (9 points total).
    Returns:
        np.ndarray: A 2D array of shape (N, 2) representing [x, z] coordinates.
            N=1 if include_corners is False; N=9 if True.
    """
    pass

def filter_valid_scene_objects(object_bboxes, whitelist_set, blacklist_set=None):
    """
    Filters raw scene objects based on category whitelists/blacklists and pre-calculates their 2D centers.
    Use this tool to clean up raw scene data and get a list of relevant objects with their locations.
    Args:
        object_bboxes (dict): The raw dictionary of object bounding boxes from scene info.
            Key is the object ID. Value is a dict with 'category', 'min' [x,y,z], and 'max' [x,y,z].
        whitelist_set (set[str]): A set of ALLOWED category names (must be lowercase strings).
            Only objects belonging to these categories will be kept.
        blacklist_set (set[str], optional): A set of FORBIDDEN category substrings (lowercase).
            If an object's category contains any of these strings, it is discarded.
            Defaults to structural elements like "wall", "floor", "ceiling".
    Returns:
        tuple: A tuple containing two elements:
            1. valid_objects_map (dict): A cleaner dictionary mapping {object_id: object_data}.
               'object_data' contains {'id', 'category', 'center_xz' (np.array)}.
            2. category_counts (Counter): A frequency count of all valid categories found.
    """
    pass

def calculate_planar_angles(vec_ref, vec_targets):
    """
    Calculates the relative clockwise/counter-clockwise angles (0-360 degrees) for multiple targets.
    This tool determines "where is the target relative to the reference direction?".
    Args:
        vec_ref (np.ndarray): A 1D reference vector of shape (2,) representing the "forward" direction
            (e.g., the direction an agent is facing).
        vec_targets (np.ndarray): A 2D array of shape (N, 2) representing vectors pointing to N targets.
    Returns:
        np.ndarray: An array of shape (N,) containing angles in DEGREES.
            - Range: [0, 360).
            - Direction: 0 is aligned with vec_ref. Angles increase counter-clockwise.
            - Logic: Uses dot product for magnitude and cross product for left/right distinction.
    """
    pass

def calculate_projected_distance(cam_pos_xz, target_pos_xz, heading_angle_deg):
    """
    Calculates how much distance is covered towards/away from a target given a movement direction.
    Use this to determine if a movement (e.g., turning) makes the agent "get closer to" or
    "get farther from" a target object.
    Args:
        cam_pos_xz (np.ndarray): The starting position of the camera/agent [x, z].
        target_pos_xz (np.ndarray): The position of the target object [x, z].
        heading_angle_deg (float): The FINAL absolute heading angle in degrees (after turning).
            Coordinate system: 0 degrees = +Z axis.
    Returns:
        float: The projected distance.
            - Positive value (>0): Moving TOWARDS the target.
            - Negative value (<0): Moving AWAY from the target.
            - Magnitude indicates the effectiveness of the movement.
    """
    pass

def is_distance_valid(triple_cats, dist_lookup, valid_objects_map, min_dist=0.30, max_dist=5.0):
    """
    Validates if a trio of objects satisfies the distance constraints for a spatial question.
    This prevents generating questions about objects that are too close (collision) or too far apart.
    It automatically calculates and caches distances using object BBoxes.
    Args:
        triple_cats (tuple[str]): A tuple of 3 category names, e.g., ('table', 'chair', 'lamp').
        dist_lookup (dict): A dictionary to cache distance results. Pass an empty dict {} initially.
            The function will update this dict to save computation time.
        valid_objects_map (dict): The dictionary returned by `filter_valid_scene_objects`.
            Must contain full object data for BBox calculation.
        min_dist (float): Minimum valid distance in meters (default 0.3).
        max_dist (float): Maximum valid distance in meters (default 5.0).
    Returns:
        bool: True if ALL pairwise distances in the triple are within [min_dist, max_dist].
    """
    pass

def is_angle_ambiguous(angles, threshold=10):
    """
    Checks if a spatial direction is ambiguous (vague) based on geometric heuristics.
    A direction is ambiguous if:
    1. The object spans across multiple quadrants (e.g., it's huge and surrounding the observer).
    2. The object's center is too close to the axis boundaries (0, 90, 180, 270 degrees).
    Args:
        angles (np.ndarray): An array of angles in degrees.
            - Index 0 MUST be the centroid's angle.
            - Indices 1+ are the angles of the object's corners.
        threshold (float): The safety margin in degrees from the axes (default 10).
    Returns:
        bool: True if the direction is ambiguous (BAD question). False if clear (GOOD question).
    """
    pass

def get_direction_label(angle_deg):
    """
    Converts a numerical angle (degrees) into a semantic direction label.
    Mapping Rules:
    - [0, 90)   -> 'front-left'
    - [90, 180) -> 'back-left'
    - [180, 270)-> 'back-right'
    - [270, 360)-> 'front-right'
    Args:
        angle_deg (float): Angle in degrees [0, 360).
    Returns:
        str: The direction label string.
    """
    pass

def get_visible_categories_per_view(visible_views_data, whitelist_set, blacklist_set=None):
    """
    Parses the raw visible views data to extract a clean list of object categories visible from each viewpoint.
    This function handles:
    1. Mapping specific angles ("0", "90", "180", "270") to indices (0, 1, 2, 3).
    2. Filtering objects based on blacklist (substring match) and whitelist (exact match).
    3. Formatting category names (capitalization).
    Args:
        visible_views_data (dict): The raw dictionary loaded from 'visible_views.json'.
            Must contain a key "views" which maps angle strings to object lists.
        whitelist_set (set[str]): A set of ALLOWED category names (must be lowercase).
        blacklist_set (set[str], optional): A set of FORBIDDEN category substrings.
            Defaults to standard structural elements if None.
    Returns:
        dict: A dictionary mapping view indices to sets of visible categories.
            Structure: {
                0: {"Chair", "Table"},  # Corresponds to angle "0"
                1: {"Sofa", "Lamp"},    # Corresponds to angle "90"
                ...
            }
            Returns an empty dict if required angles are missing.
    """
    pass

def calculate_target_view_index(start_view_idx, rotation_desc, look_direction="front"):
    """
    Simulates the camera movement and calculates the final viewpoint index based on rotation and looking direction.
    This function encodes the specific modular arithmetic logic of the Holodeck dataset:
    - View indices: 0 (North/0°), 1 (East/90°), 2 (South/180°), 3 (West/270°).
    - Rotations are additive.
    - Looking directions are additive relative to the new body orientation.
    Args:
        start_view_idx (int): The starting view index [0, 1, 2, 3].
        rotation_desc (str): Description of the body rotation.
            Supported formats:
            - "turn left 90", "left 90" -> -1
            - "turn right 90", "right 90" -> +1
            - "turn left 180", "turn right 180", "turn around" -> +2
        look_direction (str, optional): The relative direction the head/camera turns after body rotation.
            Supported values:
            - "front" (default) -> +0
            - "left" -> -1
            - "right" -> +1
            - "back", "behind" -> +2
    Returns:
        int: The final view index (0-3).
    """
    pass

def cal_3d_bbox_distance_between_categories(list_obj_A, list_obj_B):
    """
    Calculates the MINIMUM 3D distance between two groups of objects.
    Args:
        list_obj_A (list[dict]): List of object dicts (must contain 'min', 'max' or full bbox info).
        list_obj_B (list[dict]): List of object dicts.
    Returns:
        float: The minimum Euclidean distance in meters.
    """
    pass
''')

class ArchitectPrompts:

    @staticmethod
    def get_system_prompt():
        return textwrap.dedent("""
            # Role
            You are an Expert Data Architect specializing in Reverse Engineering QA Logic.
            Your goal is to analyze specific User-Provided QA Examples and generalize them into programmatic task templates.

            # Workflow
            1. **Analyze**: Read the specific QA pairs provided by the user carefully.
            2. **Generalize**: Replace specific entity names AND numbers with placeholders.
               - E.g., "chair" -> "{category}"
               - E.g., "Image 1" -> "Image {view_id}"
               - **CRITICAL**: If a number appears (e.g., "at least 1", "3 objects"), you MUST generalize it to a parameter like "{count}" or "{threshold}".
               - **[CONDITIONAL] MCQ FORMATTING**: IF the example explicitly contains multiple-choice options (e.g., A. xxx \n B. xxx), you MUST PRESERVE the A/B/C/D structure in the `question_template`. Replace the contents with placeholders like: `\\nA. {opt_a}\\nB. {opt_b}\\nC. {opt_c}\\nD. {opt_d}`. If it is NOT a multiple-choice question, ignore this rule.
               - **[CONDITIONAL] DYNAMIC DATA STRUCTURE**: IF a placeholder represents a complex collection (like a list of multiple objects, e.g., "plant, TV, bed"), you MUST explicitly describe its exact format and count in the `programmatic_hint`. (e.g., "Each option is a comma-separated list of multiple object categories"). If the placeholders are just simple numbers or single words, ignore this rule.
            3. **Define**: Create a generalized "Task Definition" that contains the exact question template string.

            # Constraint: Programmatic Verifiability
            The tasks you define must be solvable using ONLY:
            1. Object Bounding Boxes (Centroids, Dimensions) from the Schema.
            2. Camera Metadata (Position, Rotation) from the Schema.

            # Output Format (STRICT)
            Return a strictly valid JSON LIST. Use EXACTLY these keys:

            [
                {
                    "task_name": "name_of_task_snake_case",
                    "description": "Brief description of the logic.",
                    "question_template": "Question string with python format placeholders like {category}.",
                    "parameters": ["category", "count"],
                    "programmatic_hint": "Brief logic hint. (If applicable, describe the exact data structure of complex placeholders like lists/options based on the user's example)."
                }
            ]

            Do NOT wrap the list in a dictionary like {"tasks": [...]}. Return the list directly.
        """).strip()

    @staticmethod
    def get_user_prompt(qa_examples_str, bbox_schema_str, view_schema_str):
        return textwrap.dedent(f"""
            # Reference QA Examples (Ground Truth)
            I want to generate a large dataset of QA pairs that follow the logic (and phrasing) of these specific examples:

            ```text
            {qa_examples_str}
            ```

            # Available Data Structure (Schema)
            You need to map the logic above to these data structures:

            ## 1. Objects (bbox)
            ```json
            {bbox_schema_str}
            ```

            ## 2. Views (camera)
            ```json
            {view_schema_str}
            ```

            # Task
            Analyze the examples above.
            Extract the **Task Types** and create **Question Templates** with `{{placeholders}}` for variable parts (especially numbers and object names).

            Return ONLY the JSON list.
        """).strip()

class CoderPrompts:
    @staticmethod
    def get_system_prompt():
        return textwrap.dedent(f"""
            # Role
            You are an Expert Python Developer for Holodeck QA Generation.
            Inherit from `base_qa_generator.BaseQAGenerator`.

            # LIBRARY REFERENCE
            ```python
            {{UTILS_INTERFACE_STR}}
            ```

            # CRITICAL PYTHON SYNTAX & OUTPUT RULES (MUST FOLLOW)
            1. **FULL SCRIPT REQUIREMENT**: You MUST return the ENTIRE, fully functional Python script based on the provided SKELETON. Do NOT omit the imports, the class definition, or the `def generate_scene_qa` signature.
            2. **INDENTATION**: The code you write to replace `# [YOUR CODE HERE]` MUST be indented by exactly 20 spaces so it correctly aligns inside the `generate_scene_qa` method.
            3. `self.args` is an `argparse.Namespace` object. ❌ FORBIDDEN: `self.args.get('key')`. ✅ REQUIRED: `getattr(self.args, 'key', default)`.
            4. **STRICT OPTION ALIGNMENT**: If a question has predefined choices, your calculated `answer` MUST EXACTLY MATCH one of the strings in the `options` list.
            5. **UNIVERSAL MCQ ANSWER FORMATTING (CRITICAL)**: IF the `parameters` list includes `opt_a`, `opt_b`, `opt_c`, `opt_d` (meaning it is an explicit Multiple-Choice question):
               - You MUST map your shuffled `options_list` elements to these keys in `format_kwargs` (e.g., `'opt_a': options_list[0]`, etc.).
               - You MUST override the basic answer logic to compute the correct alphabetical letter. E.g.:
                 `correct_idx = options_list.index(raw_answer)`
                 `answer = f"{{chr(65 + correct_idx)}}. {{raw_answer}}"` (This ensures the output looks like "B. 1" or "C. chair").
            6. **NO MARKDOWN TAGS (CRITICAL)**: You MUST output pure, raw Python code ONLY. DO NOT wrap your output in ```python ... ``` or any other markdown formatting. The very first line of your output MUST be the `import os` statement.
            7. **DIRECT ANSWER FORMATTING (CRITICAL)**: IF the question does NOT require multiple-choice options (i.e., NO `opt_a`, `opt_b` in parameters) and is not a standard Yes/No question, you MUST set `'options': None` and return the exact raw string/number as the `answer`. DO NOT forcefully generate distractors or options lists.
            8. **JSON SERIALIZATION SAFETY (CRITICAL)**: You MUST explicitly cast all Numpy variables (e.g., `np.float64`, `np.bool_`, `numpy.int64`) to native Python types using `float()`, `bool()`, or `int()` before adding them to the `qa_pair` or `metadata` dictionaries. Do NOT put raw Numpy types into the JSON output, or it will crash.

            # SPECIFIC TASK RULES

            ## TASK CATEGORY 1: "Distance Measurement" (Exactly 2 Objects)
            - **VALIDATION LOGIC (STRICTLY FOLLOW)**:
              ```python
              category_counts = Counter(obj['category'] for obj in valid_objects_dict.values())
              strategy_objects = [obj for obj in valid_objects_dict.values() if category_counts[obj['category']] == 1]
              if len(strategy_objects) < 2: return []

              seen_combinations = set()
              for obj_a, obj_b in itertools.combinations(strategy_objects, 2):
                  combo_sig = frozenset([obj_a['category'], obj_b['category']])
                  if combo_sig in seen_combinations: continue

                  dist = self.get_aabb_dist(obj_a, obj_b)
                  if dist < 0.1: continue
                  seen_combinations.add(combo_sig)

                  format_kwargs = {{
                      # DYNAMIC MAPPING here
                  }}
                  question = QUESTION_TEMPLATE.format(**format_kwargs)

                  qa_pair = {{
                      'scene_name': scene_name,
                      'question': question,
                      'answer': f"{{dist:.2f}}",
                      'options': None,
                      'metadata': {{
                          'question_type': getattr(self.args, 'question_type', 'object_distance_measurement'),
                          'distance': dist
                      }}
                  }}
                  scene_qa_list.append(qa_pair)
                  if len(scene_qa_list) >= getattr(self.args, 'num_subsample', 20): break
              ```

            ## TASK CATEGORY 2: "Proximity Comparison (Standard & Negative Sampling)"
            - **VALIDATION LOGIC (STRICTLY FOLLOW)**:
              ```python
              import re
              category_counts = Counter(obj['category'] for obj in valid_objects_dict.values())
              strategy_objects = [obj for obj in valid_objects_dict.values() if category_counts[obj['category']] == 1]

              # ---> [INTERCEPT] Negative Sampling Early Exit <---
              q_type = getattr(self.args, 'question_type', '').lower()
              if 'negative' in q_type:
                  global_vocab = ['bicycle', 'piano', 'sofa', 'lamp', 'tv', 'bed', 'rug', 'guitar', 'oven', 'refrigerator', 'motorcycle', 'book', 'plant', 'chair', 'cabinet', 'table', 'laptop', 'monitor', 'keyboard', 'shoes', 'backpack', 'clock', 'mirror', 'fan', 'trash can']
                  scene_cats = [obj['category'] for obj in valid_objects_dict.values()]
                  disjoint_cats = [g for g in global_vocab if not any(g in s or s in g for s in scene_cats)]
                  if not disjoint_cats or len(strategy_objects) < 1: return []

                  fallback_ans = "None of the candidates were found in the picture."

                  for _ in range(getattr(self.args, 'num_subsample', 20)):
                      ref_obj = random.choice(strategy_objects)
                      fakes = random.sample(disjoint_cats, min(4, len(disjoint_cats)))

                      format_kwargs = {{'obj1': ref_obj['category']}}
                      if 'opt_a' in getattr(self.args, 'parameters', []):
                          format_kwargs.update({{'opt_a': fakes[0], 'opt_b': fakes[1], 'opt_c': fakes[2], 'opt_d': fakes[3] if len(fakes)>3 else fakes[0]}})

                      question = QUESTION_TEMPLATE.format(**format_kwargs)
                      question = re.sub(r'\\s*[A-Z]\\.\\s*$', '', question).strip()

                      qa_pair = {{
                          'scene_name': scene_name, 'question': question, 'answer': fallback_ans, 'options': None,
                          'metadata': {{'question_type': getattr(self.args, 'question_type', 'negative_sampling')}}
                      }}
                      scene_qa_list.append(qa_pair)
                  return scene_qa_list # 🚨 EARLY EXIT

              # ---> [STANDARD LOGIC] <---
              seen_combinations = set()
              for combo in itertools.permutations(strategy_objects, len(getattr(self.args, 'parameters', []))):
                  target = combo[0]
                  candidates = combo[1:]

                  combo_sig = (target['category'], frozenset(c['category'] for c in candidates))
                  if combo_sig in seen_combinations: continue

                  dists = [self.get_aabb_dist(target, c) for c in candidates]
                  if any(d < 0.1 for d in dists): continue

                  sorted_dists = sorted(dists)
                  if len(sorted_dists) > 1 and sorted_dists[1] - sorted_dists[0] < 0.5: continue
                  seen_combinations.add(combo_sig)

                  format_kwargs = {{'obj1': target['category']}}
                  opts_keys = [k for k in getattr(self.args, 'parameters', []) if k.startswith('opt_')]
                  for i, k in enumerate(opts_keys):
                      format_kwargs[k] = candidates[i]['category'] if i < len(candidates) else candidates[-1]['category']

                  question = QUESTION_TEMPLATE.format(**format_kwargs)
                  question = re.sub(r'\\s*[A-Z]\\.\\s*$', '', question).strip()

                  correct_idx = dists.index(sorted_dists[0])
                  answer = candidates[correct_idx]['category']

                  qa_pair = {{
                      'scene_name': scene_name, 'question': question, 'answer': answer,
                      'options': [c['category'] for c in candidates],
                      'metadata': {{'question_type': getattr(self.args, 'question_type', 'proximity_comparison')}}
                  }}
                  scene_qa_list.append(qa_pair)
                  if len(scene_qa_list) >= getattr(self.args, 'num_subsample', 20): break
              ```

            ## TASK CATEGORY 3: "Counting & Existence (Exact Count / Yes-No)"
            - **Condition**: Tasks asking for exact numbers ("How many") OR checking if an object exists ("Is there a...").
            - **CRITICAL RULE**: The LLM MUST deduce the intent based on the `QUESTION_TEMPLATE`. If it asks for a Boolean Yes/No, use BRANCH A. If it asks for an exact number, use BRANCH B.
            - **VALIDATION LOGIC SKELETON**:
              ```python
              # ===== LLM MUST CHOOSE EITHER BRANCH A OR BRANCH B BASED ON QUESTION TEMPLATE =====

              # ---> [BRANCH A] IF INTENT IS "EXISTENCE" (YES/NO) <---
              scene_cats = list(set([obj['category'] for obj in valid_objects_dict.values()]))
              global_vocab = ['bicycle', 'piano', 'sofa', 'lamp', 'tv', 'bed', 'rug', 'guitar', 'oven', 'refrigerator', 'motorcycle', 'book', 'plant', 'chair', 'cabinet', 'table', 'laptop', 'monitor', 'keyboard', 'shoes', 'backpack', 'clock', 'mirror', 'fan', 'trash can']

              # Filter out global vocab that overlaps with scene to avoid ambiguity
              disjoint_cats = []
              for g_cat in global_vocab:
                  is_overlapping = False
                  for s_cat in scene_cats:
                      if g_cat in s_cat or s_cat in g_cat: is_overlapping = True; break
                  if not is_overlapping: disjoint_cats.append(g_cat)

              # Generate YES questions from actual objects
              for cat in scene_cats:
                  format_kwargs = {{'category': cat}} # Ensure mapping matches parameters
                  question = QUESTION_TEMPLATE.format(**format_kwargs)
                  qa_pair = {{
                      'scene_name': scene_name, 'question': question, 'answer': 'Yes', 'options': None,
                      'metadata': {{'question_type': getattr(self.args, 'question_type', 'existence'), 'category': cat, 'exists': True}}
                  }}
                  scene_qa_list.append(qa_pair)

              # Generate NO questions from disjoint objects
              random.shuffle(disjoint_cats)
              for cat in disjoint_cats[:len(scene_cats)]:
                  format_kwargs = {{'category': cat}}
                  question = QUESTION_TEMPLATE.format(**format_kwargs)
                  qa_pair = {{
                      'scene_name': scene_name, 'question': question, 'answer': 'No', 'options': None,
                      'metadata': {{'question_type': getattr(self.args, 'question_type', 'existence'), 'category': cat, 'exists': False}}
                  }}
                  scene_qa_list.append(qa_pair)

              random.shuffle(scene_qa_list)
              scene_qa_list = scene_qa_list[:getattr(self.args, 'num_subsample', 20)]


              # ---> [BRANCH B] IF INTENT IS "COUNTING" (EXACT NUMBER) <---
              all_categories = [obj['category'] for obj in valid_objects_dict.values()]
              category_counts = Counter(all_categories)

              for category, actual_count in category_counts.items():
                  raw_answer = str(actual_count)
                  options_set = {{raw_answer, str(max(0, actual_count - 1)), str(actual_count + 1), str(actual_count + random.randint(2, 4))}}
                  options_list = list(options_set)

                  while len(options_list) < 4:
                      options_list.append(str(actual_count + random.randint(5, 10)))
                      options_list = list(set(options_list))
                  options_list = options_list[:4]
                  random.shuffle(options_list)

                  format_kwargs = {{'category': category}} # Ensure mapping matches parameters

                  if 'opt_a' in getattr(self.args, 'parameters', []):
                      format_kwargs.update({{'opt_a': options_list[0], 'opt_b': options_list[1], 'opt_c': options_list[2], 'opt_d': options_list[3]}})
                      correct_idx = options_list.index(raw_answer)
                      final_answer = f"{{chr(65 + correct_idx)}}. {{raw_answer}}"
                  else:
                      final_answer = raw_answer

                  question = QUESTION_TEMPLATE.format(**format_kwargs)
                  qa_pair = {{
                      'scene_name': scene_name, 'question': question, 'answer': final_answer,
                      'options': options_list if 'opt_a' in getattr(self.args, 'parameters', []) else None,
                      'metadata': {{'question_type': getattr(self.args, 'question_type', 'count'), 'category': category, 'actual_count': actual_count}}
                  }}
                  scene_qa_list.append(qa_pair)
                  if len(scene_qa_list) >= getattr(self.args, 'num_subsample', 20): break
              ```

            ## TASK CATEGORY 4: "Spatial / Directional Relation (Standard & Negative Sampling)"
            - **Condition**: Tasks asking about relative positions, directions, OR testing negative sampling.
            - **CRITICAL RULE**: Handle direct answers, MCQ, AND Negative Sampling. Use `question_type` to trigger Early Exit.
            - **VALIDATION LOGIC SKELETON**:
              ```python
              category_counts = Counter(obj['category'] for obj in valid_objects_dict.values())
              strategy_objects = [obj for obj in valid_objects_dict.values() if category_counts[obj['category']] == 1]
              if len(strategy_objects) < 3: return []

              # ---> [INTERCEPT] Negative Sampling Early Exit <---
              q_type = getattr(self.args, 'question_type', '').lower()
              if 'negative' in q_type:
                  global_vocab = ['bicycle', 'piano', 'sofa', 'lamp', 'tv', 'bed', 'rug', 'guitar', 'oven', 'refrigerator', 'motorcycle', 'book', 'plant', 'chair', 'cabinet', 'table', 'laptop', 'monitor', 'keyboard', 'shoes', 'backpack', 'clock', 'mirror', 'fan', 'trash can']
                  scene_cats = [obj['category'] for obj in valid_objects_dict.values()]
                  disjoint_cats = [g for g in global_vocab if not any(g in s or s in g for s in scene_cats)]
                  if not disjoint_cats: return []

                  fallback_ans = "The orienting object or querying object is not found in the picture."

                  for _ in range(getattr(self.args, 'num_subsample', 20)):
                      reals = random.sample(strategy_objects, 2)
                      fake_obj = random.choice(disjoint_cats)

                      format_kwargs = {{}}
                      if 'obj1' in getattr(self.args, 'parameters', []): format_kwargs['obj1'] = reals[0]['category']
                      if 'obj2' in getattr(self.args, 'parameters', []): format_kwargs['obj2'] = reals[1]['category']
                      if 'obj3' in getattr(self.args, 'parameters', []): format_kwargs['obj3'] = fake_obj

                      if 'opt_a' in getattr(self.args, 'parameters', []):
                          fakes = random.sample(disjoint_cats, min(4, len(disjoint_cats)))
                          format_kwargs.update({{'opt_a': fakes[0], 'opt_b': fakes[1], 'opt_c': fakes[2], 'opt_d': fakes[3] if len(fakes)>3 else fakes[0]}})

                      question = QUESTION_TEMPLATE.format(**format_kwargs)

                      qa_pair = {{
                          'scene_name': scene_name, 'question': question, 'answer': fallback_ans, 'options': None,
                          'metadata': {{'question_type': getattr(self.args, 'question_type', 'negative_sampling')}}
                      }}
                      scene_qa_list.append(qa_pair)
                  return scene_qa_list # 🚨 EARLY EXIT: Skip all spatial math!

              # ---> [STANDARD LOGIC] Branches A (MCQ) & B (Direct) <---
              seen_combinations = set()
              for ref_obj, face_obj, target_obj in itertools.permutations(strategy_objects, 3):
                  combo_sig = frozenset([ref_obj['category'], face_obj['category'], target_obj['category']])
                  if combo_sig in seen_combinations: continue

                  dist_ref_target = self.get_aabb_dist(ref_obj, target_obj)
                  dist_ref_face = self.get_aabb_dist(ref_obj, face_obj)
                  if dist_ref_target < 0.1 or dist_ref_face < 0.1: continue

                  ref_pos = (ref_obj['min'] + ref_obj['max']) / 2.0
                  face_pos = (face_obj['min'] + face_obj['max']) / 2.0
                  target_pos = (target_obj['min'] + target_obj['max']) / 2.0

                  fwd_vec = face_pos - ref_pos
                  fwd_vec[1] = 0
                  if np.linalg.norm(fwd_vec) < 1e-6: continue
                  fwd_vec = fwd_vec / np.linalg.norm(fwd_vec)

                  tgt_vec = target_pos - ref_pos
                  tgt_vec[1] = 0
                  if np.linalg.norm(tgt_vec) < 1e-6: continue
                  tgt_vec = tgt_vec / np.linalg.norm(tgt_vec)

                  dot = np.dot(fwd_vec, tgt_vec)
                  cross = fwd_vec[0] * tgt_vec[2] - fwd_vec[2] * tgt_vec[0]
                  angle_deg = np.degrees(np.arctan2(cross, dot)) % 360

                  global_ideal_angles = {{'front': 0, 'front-left': 45, 'left': 90, 'back-left': 135, 'back': 180, 'back-right': 225, 'right': 270, 'front-right': 315}}
                  best_dir = min(global_ideal_angles.keys(), key=lambda k: min(abs(angle_deg - global_ideal_angles[k]), 360 - abs(angle_deg - global_ideal_angles[k])))

                  format_kwargs = {{'obj1': ref_obj['category'], 'obj2': face_obj['category'], 'obj3': target_obj['category']}}

                  if 'opt_a' in getattr(self.args, 'parameters', []):
                      task_options = [best_dir]
                      distractors = [d for d in global_ideal_angles.keys() if d != best_dir]
                      random.shuffle(distractors)

                      for d in distractors:
                          task_options.append(d)
                          if len(task_options) == 4: break

                      random.shuffle(task_options)
                      format_kwargs.update({{'opt_a': task_options[0], 'opt_b': task_options[1], 'opt_c': task_options[2], 'opt_d': task_options[3]}})
                      correct_idx = task_options.index(best_dir)
                      final_answer = f"{{chr(65 + correct_idx)}}. {{best_dir}}"
                      final_options = task_options
                  else:
                      final_answer = best_dir
                      final_options = None

                  seen_combinations.add(combo_sig)
                  question = QUESTION_TEMPLATE.format(**format_kwargs)

                  qa_pair = {{
                      'scene_name': scene_name, 'question': question, 'answer': final_answer, 'options': final_options,
                      'metadata': {{'question_type': getattr(self.args, 'question_type', 'relative_direction')}}
                  }}
                  scene_qa_list.append(qa_pair)
                  if len(scene_qa_list) >= getattr(self.args, 'num_subsample', 20): break
              ```

            ## TASK CATEGORY 5: "Numeric Properties (Global Scene or Single Object)"
            - **Condition**: Tasks asking for a numeric measurement (e.g., room size, volume, area) of the scene or a single object.
            - **CRITICAL RULE**: Handle BOTH direct answers (options: None) AND multiple-choice (generate numeric distractors if 'opt_a' is in parameters).
            - **VALIDATION LOGIC SKELETON**:
              ```python
              # 1. Target Identification
              is_global = 'obj1' not in getattr(self.args, 'parameters', [])
              items_to_process = []

              if is_global:
                  target_value = scene_info.get('room_size') # Deduce actual key based on task
                  if target_value is not None: items_to_process.append((None, float(target_value)))
              else:
                  category_counts = Counter(obj['category'] for obj in valid_objects_dict.values())
                  strategy_objects = [obj for obj in valid_objects_dict.values() if category_counts[obj['category']] == 1]
                  for obj in strategy_objects:
                      dims = obj['max'] - obj['min']
                      val = float(np.prod(dims)) # Deduce property (e.g., volume, area) from template
                      if val > 0.001: items_to_process.append((obj, val))

              if not items_to_process: return []

              # 2. Dynamic Option Generation & Output
              for obj, target_value in items_to_process:
                  format_kwargs = {{'obj1': obj['category']}} if obj else {{}}
                  raw_answer = f"{{target_value:.2f}}"

                  # ---> [MCQ BRANCH] Generate Distractors dynamically <---
                  if 'opt_a' in getattr(self.args, 'parameters', []):
                      options_set = {{raw_answer, f"{{target_value * 0.8:.2f}}", f"{{target_value * 1.25:.2f}}", f"{{target_value + 2.5:.2f}}"}}
                      options_list = list(options_set)
                      while len(options_list) < 4:
                          options_list.append(f"{{target_value * random.uniform(0.5, 1.5):.2f}}")
                          options_list = list(set(options_list))
                      options_list = options_list[:4]
                      random.shuffle(options_list)

                      format_kwargs.update({{'opt_a': options_list[0], 'opt_b': options_list[1], 'opt_c': options_list[2], 'opt_d': options_list[3]}})
                      correct_idx = options_list.index(raw_answer)
                      final_answer = f"{{chr(65 + correct_idx)}}. {{raw_answer}}"
                      final_options = options_list

                  # ---> [DIRECT BRANCH] Open-Ended <---
                  else:
                      final_answer = raw_answer
                      final_options = None

                  question = QUESTION_TEMPLATE.format(**format_kwargs)

                  qa_pair = {{
                      'scene_name': scene_name, 'question': question, 'answer': final_answer, 'options': final_options,
                      'metadata': {{'question_type': getattr(self.args, 'question_type', 'numeric_property')}}
                  }}
                  scene_qa_list.append(qa_pair)
                  if len(scene_qa_list) >= getattr(self.args, 'num_subsample', 20): break
              ```

            ## TASK CATEGORY 6: "Set / Attribute Verification (Multiple Choice)"
            - **Condition**: Tasks explicitly asking to check SET INTERSECTIONS or verify LISTS of objects (e.g., "Which option does not contain..."). **CRITICAL: DO NOT use this category for Spatial, Counting, or Viewpoint questions, even if they have opt_a/opt_b.**
            - **DATA STRUCTURE STRICT RULE**: You MUST read the `programmatic_hint` to determine if each option should be a SINGLE object or a COMMA-SEPARATED LIST of multiple objects.
            - **CRITICAL ANTI-AMBIGUITY RULE**: You MUST filter `global_vocab` to ensure NO substring or word-level overlap with `scene_cats` (e.g., "chair" vs "meeting chair").
            - **VALIDATION LOGIC SKELETON**:
              ```python
              scene_cats = list(set([obj['category'] for obj in valid_objects_dict.values()]))
              global_vocab = ['bicycle', 'piano', 'sofa', 'lamp', 'tv', 'bed', 'rug', 'guitar', 'oven', 'refrigerator', 'motorcycle', 'book', 'plant', 'chair', 'cabinet', 'table', 'laptop', 'monitor', 'keyboard', 'shoes', 'backpack', 'clock', 'mirror', 'fan', 'trash can']

              # Robust semantic filtering to prevent hypernym ambiguity (e.g. "chair" vs "meeting chair")
              disjoint_cats = []
              for g_cat in global_vocab:
                  is_overlapping = False
                  for s_cat in scene_cats:
                      if g_cat in s_cat or s_cat in g_cat:
                          is_overlapping = True; break
                      g_words = set(re.findall(r'\\w+', g_cat))
                      s_words = set(re.findall(r'\\w+', s_cat))
                      if g_words.intersection(s_words):
                          is_overlapping = True; break
                  if not is_overlapping:
                      disjoint_cats.append(g_cat)

              if len(disjoint_cats) < 4: return []

              for _ in range(getattr(self.args, 'num_subsample', 20)):
                  correct_items = random.sample(disjoint_cats, min(3, len(disjoint_cats)))
                  correct_option = ", ".join(correct_items)

                  options_list = [correct_option]
                  for _ in range(3):
                      num_scene = random.randint(1, min(2, len(scene_cats)))
                      distractor = random.sample(scene_cats, num_scene) + random.sample(disjoint_cats, max(0, 3 - num_scene))
                      random.shuffle(distractor)
                      options_list.append(", ".join(distractor))

                  random.shuffle(options_list)

                  format_kwargs = {{
                      'opt_a': options_list[0], 'opt_b': options_list[1],
                      'opt_c': options_list[2], 'opt_d': options_list[3]
                  }}
                  question = QUESTION_TEMPLATE.format(**format_kwargs)

                  correct_idx = options_list.index(correct_option)
                  final_answer = f"{{chr(65 + correct_idx)}}. {{correct_option}}"

                  qa_pair = {{
                      'scene_name': scene_name,
                      'question': question,
                      'answer': final_answer,
                      'options': options_list,
                      'metadata': {{'question_type': getattr(self.args, 'question_type', 'set_verification')}}
                  }}
                  scene_qa_list.append(qa_pair)
              ```

            ## TASK CATEGORY 7: "Descriptive Spatial / Viewpoint Relation (MCQ)"
            - **Condition**: Tasks asking to evaluate full-sentence spatial descriptions from a specific viewpoint (e.g., "When viewing from the entrance...").
            - **CRITICAL RULE**: Divide the room into a strict 3x3 logical grid based on the ROOM'S GEOMETRIC CENTER and its walls. DO NOT use diagonal raycasts.
            - **VALIDATION LOGIC SKELETON**:
              ```python
              # 1. Count categories to ensure uniqueness
              category_counts = Counter(obj['category'] for obj in valid_objects_dict.values())

              # 2. Identify the viewpoint/reference object (e.g., 'door' for entrance)
              ref_candidates = [obj for obj in valid_objects_dict.values() if 'door' in obj['category'] or 'entrance' in obj['category']]
              if not ref_candidates: return []
              ref_obj = ref_candidates[0]
              ref_pos = (ref_obj['min'] + ref_obj['max']) / 2.0
              ref_pos[1] = 0 # Flatten to XZ plane

              # 3. Establish TRUE Geometric Room Center & Room Size
              room_min = np.min([obj['min'] for obj in valid_objects_dict.values()], axis=0)
              room_max = np.max([obj['max'] for obj in valid_objects_dict.values()], axis=0)
              room_min[1] = 0; room_max[1] = 0
              room_center = (room_min + room_max) / 2.0
              room_size = room_max - room_min

              # 4. Snap Viewing Direction to Room Walls (Orthogonal Grid)
              door_to_center = room_center - ref_pos
              if abs(door_to_center[0]) > abs(door_to_center[2]):
                  right_axis = np.array([0, 0, -1]) if door_to_center[0] > 0 else np.array([0, 0, 1])
                  room_width = room_size[2]
              else:
                  right_axis = np.array([1, 0, 0]) if door_to_center[2] > 0 else np.array([-1, 0, 0])
                  room_width = room_size[0]

              if room_width < 0.1: room_width = 1.0

              # 5. Collect target objects
              targets = [obj for obj in valid_objects_dict.values()
                         if obj['id'] != ref_obj['id'] and category_counts[obj['category']] == 1]
              if len(targets) < 4: return []

              spatial_data = []
              for t in targets:
                  pos = (t['min'] + t['max']) / 2.0
                  pos[1] = 0
                  dist = np.linalg.norm(pos - ref_pos)

                  # [CRITICAL FIX] Distance from ROOM CENTER purely parallel to the walls
                  lateral_dist = np.dot(pos - room_center, right_axis)
                  norm_proj = lateral_dist / room_width

                  if norm_proj > 0.166:
                      lr_dir = "right"
                  elif norm_proj < -0.166:
                      lr_dir = "left"
                  else:
                      lr_dir = "center"

                  spatial_data.append({{
                      'category': t['category'],
                      'dir': lr_dir,
                      'dist': dist
                  }})

              spatial_data.sort(key=lambda x: x['dist']) # Sort by depth

              for _ in range(getattr(self.args, 'num_subsample', 20)):
                  true_target = random.choice(spatial_data)
                  true_desc = f"The {{true_target['category']}} is on the {{true_target['dir']}} side."

                  if random.random() < 0.3:
                      true_desc = f"The {{spatial_data[-1]['category']}} is the farthest object."

                  distractors = []
                  while len(distractors) < 3:
                      false_target = random.choice(spatial_data)
                      false_dirs = ["left", "right", "center"]
                      if false_target['dir'] in false_dirs: false_dirs.remove(false_target['dir'])
                      false_desc = f"The {{false_target['category']}} is on the {{random.choice(false_dirs)}} side."

                      if random.random() < 0.2:
                          wrong_farthest = random.choice(spatial_data[:-1])
                          false_desc = f"The {{wrong_farthest['category']}} is the farthest object."

                      if false_desc != true_desc and false_desc not in distractors:
                          distractors.append(false_desc)

                  options_list = [true_desc] + distractors
                  random.shuffle(options_list)

                  format_kwargs = {{
                      'opt_a': options_list[0], 'opt_b': options_list[1],
                      'opt_c': options_list[2], 'opt_d': options_list[3]
                  }}
                  question = QUESTION_TEMPLATE.format(**format_kwargs)

                  correct_idx = options_list.index(true_desc)
                  final_answer = f"{{chr(65 + correct_idx)}}. {{true_desc}}"

                  qa_pair = {{
                      'scene_name': scene_name,
                      'question': question,
                      'answer': final_answer,
                      'options': options_list,
                      'metadata': {{'question_type': getattr(self.args, 'question_type', 'viewpoint_spatial')}}
                  }}
                  scene_qa_list.append(qa_pair)
              ```

            ## TASK CATEGORY 8: "Dimensional / Size Comparison (MCQ & Yes/No Fact Validation)"
            - **Condition**: Tasks asking to compare dimensions, volumes, or sizes between two objects.
            - **CRITICAL RULE**: If parameters include 'opt_a', use BRANCH A (MCQ). If it is a direct Yes/No question, use BRANCH B.
            - **VALIDATION LOGIC SKELETON**:
              ```python
              category_counts = Counter(obj['category'] for obj in valid_objects_dict.values())
              strategy_objects = [obj for obj in valid_objects_dict.values() if category_counts[obj['category']] == 1]
              if len(strategy_objects) < 2: return []

              seen_combinations = set()
              for obj_a, obj_b in itertools.combinations(strategy_objects, 2):
                  combo_sig = frozenset([obj_a['category'], obj_b['category']])
                  if combo_sig in seen_combinations: continue

                  dims_a = obj_a['max'] - obj_a['min']
                  dims_b = obj_b['max'] - obj_b['min']
                  vol_a = float(np.prod(dims_a))
                  vol_b = float(np.prod(dims_b))

                  if abs(vol_a - vol_b) < 0.05 and abs(dims_a[1] - dims_b[1]) < 0.1: continue
                  seen_combinations.add(combo_sig)

                  format_kwargs = {{'obj1': obj_a['category'], 'obj2': obj_b['category']}}

                  # ---> [BRANCH A] MCQ Dimensional Comparison <---
                  if 'opt_a' in getattr(self.args, 'parameters', []):
                      is_a_taller = dims_a[1] > dims_b[1]
                      correct_desc = f"The {{obj_a['category']}} is taller than the {{obj_b['category']}}." if is_a_taller else f"The {{obj_b['category']}} is taller than the {{obj_a['category']}}."
                      false_desc_1 = f"The {{obj_b['category']}} is taller than the {{obj_a['category']}}." if is_a_taller else f"The {{obj_a['category']}} is taller than the {{obj_b['category']}}."
                      false_desc_2 = f"The {{obj_a['category']}} and {{obj_b['category']}} are exactly the same height."

                      available_cats = [obj['category'] for obj in valid_objects_dict.values() if obj['category'] not in combo_sig]
                      random_cat = random.choice(available_cats) if available_cats else "wall"
                      false_desc_3 = f"The {{random_cat}} is taller than the {{obj_a['category']}}."

                      options_list = [correct_desc, false_desc_1, false_desc_2, false_desc_3]
                      random.shuffle(options_list)
                      format_kwargs.update({{'opt_a': options_list[0], 'opt_b': options_list[1], 'opt_c': options_list[2], 'opt_d': options_list[3]}})

                      correct_idx = options_list.index(correct_desc)
                      final_answer = f"{{chr(65 + correct_idx)}}. {{correct_desc}}"
                      final_options = options_list

                  # ---> [BRANCH B] Yes/No Fact Validation <---
                  else:
                      final_answer = "yes" if vol_a < vol_b else "no"
                      final_options = None

                  question = QUESTION_TEMPLATE.format(**format_kwargs)

                  qa_pair = {{
                      'scene_name': scene_name,
                      'question': question,
                      'answer': final_answer,
                      'options': final_options,
                      'metadata': {{
                          'question_type': getattr(self.args, 'question_type', 'dimensional_comparison')
                      }}
                  }}
                  scene_qa_list.append(qa_pair)
                  if len(scene_qa_list) >= getattr(self.args, 'num_subsample', 20): break
              ```

            ## TASK CATEGORY 9: "Regex String Extraction (e.g., Room Type)"
            - **Condition**: Tasks asking to identify a property embedded in a string (e.g., room type inside parentheses of an object's ID or name).
            - **CRITICAL RULE**: Do not use predefined mapping dictionaries. Use standard regex to extract the target string from the scene data, and set `options: None` for direct open-ended answers.
            - **VALIDATION LOGIC SKELETON**:
              ```python
              extracted_val = None
              # [CRITICAL] Loop through raw all_bboxes to access 'object_name', because valid_objects_dict strips it.
              for raw_obj in all_bboxes.values():
                  target_str = str(raw_obj.get('object_name', raw_obj.get('id', '')))
                  match = re.search(r'\\((.*?)\\)', target_str)
                  if match:
                      extracted_val = match.group(1).strip()
                      break

              if not extracted_val: return []

              format_kwargs = {{}} # Apply mappings if required by template
              question = QUESTION_TEMPLATE.format(**format_kwargs)

              qa_pair = {{
                  'scene_name': scene_name,
                  'question': question,
                  'answer': extracted_val,
                  'options': None, # Critical: Direct string answer
                  'metadata': {{'question_type': getattr(self.args, 'question_type', 'metadata_extraction')}}
              }}
              scene_qa_list.append(qa_pair)
              ```

            ## TASK CATEGORY 10: "Egocentric Proximity (Closest/Farthest to You/Camera)"
            - **Condition**: Tasks asking spatial relations relative to the observer ("you", "camera").
            - **CRITICAL RULE**: Extract camera position from `visible_data` and calculate Euclidean distances to object bounding boxes. Return exact object name with `options: None`.
            - **VALIDATION LOGIC SKELETON**:
              ```python
              if 'views' not in visible_data or not visible_data['views']: return []

              # Retrieve the camera position from the first available view metadata
              first_view = list(visible_data['views'].values())[0]
              cam_pos = np.array(first_view.get('camera_position', [0.0, 0.0, 0.0]))

              min_dist = float('inf')
              closest_category = None

              for obj in valid_objects_dict.values():
                  # Calculate distance from camera to the bounding box
                  delta = np.maximum(0, np.maximum(obj['min'] - cam_pos, cam_pos - obj['max']))
                  dist = float(np.linalg.norm(delta))

                  if dist < min_dist:
                      min_dist = dist
                      closest_category = obj['category']

              if not closest_category: return []

              format_kwargs = {{}}
              question = QUESTION_TEMPLATE.format(**format_kwargs)

              qa_pair = {{
                  'scene_name': scene_name,
                  'question': question,
                  'answer': closest_category,
                  'options': None, # Critical: Direct string answer
                  'metadata': {{'question_type': getattr(self.args, 'question_type', 'egocentric_proximity')}}
              }}
              scene_qa_list.append(qa_pair)
              ```

        """).strip()


    @staticmethod
    def get_user_prompt(task_meta, bbox_schema_str, view_schema_str, utils_docstring):
        class_name = f"{task_meta['task_name'].title().replace('_', '')}QAGenerator"

        return textwrap.dedent(f"""
            # Task: **{task_meta['task_name']}**
            - Template: "{task_meta['question_template']}"
            - Parameters: {task_meta.get('parameters', [])}
            - Description: {task_meta.get('description', '')}

            # SKELETON (STRICT IMPORTS & DATA LOADING)
            **CRITICAL INSTRUCTION**: You MUST output the complete code below from `import os` down to `generator.run()`. DO NOT skip or abbreviate the class definition. ONLY replace the `# [YOUR CODE HERE]` comment with the task logic.
            **CRITICAL RULE 6 ENFORCEMENT**: DO NOT output ```python or ``` tags around your final response. I am piping your output directly into a .py file!

            import os
            import json
            import random
            import itertools
            import numpy as np
            import re
            from collections import Counter
            from base_qa_generator import BaseQAGenerator

            from Utils import (
                get_viewpoint_vectors, get_bbox_projection, is_spatial_relation_satisfied,
                get_object_xz_points, calculate_planar_angles, calculate_projected_distance,
                is_angle_ambiguous, get_direction_label, get_visible_categories_per_view,
                calculate_target_view_index
            )

            QUESTION_TEMPLATE = "{task_meta['question_template']}"

            class {class_name}(BaseQAGenerator):
                def get_default_args(self):
                    return {{
                        'question_template': None,
                        'num_subsample': 20,
                        'question_type': '{task_meta['task_name']}',
                        'output_filename_prefix': 'qa_{task_meta['task_name']}',
                        'dataset': 'holodeck',
                        'parameters': {task_meta.get('parameters', [])}
                    }}

                def get_aabb_dist(self, objA, objB):
                    delta = np.maximum(0, np.maximum(objA['min'] - objB['max'], objB['min'] - objA['max']))
                    return float(np.linalg.norm(delta))

                def generate_scene_qa(self, scene_name, scene_info, frame_dirs):
                    scene_qa_list = []
                    scene_path = frame_dirs['scene_path']
                    print(f"\\n>>> [DEBUG STDOUT] Starting scene: {{scene_name}}")

                    # NOTE: scene_info contains global metadata (e.g. scene_info.get('room_size'))
                    # and nested object data (scene_info.get('object_bboxes')).

                    visible_data = self._load_json(os.path.join(scene_path, scene_name + "_visible_views.json"))
                    if not visible_data:
                        print(">>> [DEBUG] visible_views.json is empty or not found.")
                        return []

                    all_bboxes = scene_info.get('object_bboxes', {{}})
                    valid_objects_dict = {{}}

                    if 'views' in visible_data:
                        for view_id, view_data in visible_data['views'].items():
                            for vis_obj in view_data.get('visible_objects', []):
                                oid = vis_obj.get('id')
                                if oid and oid in all_bboxes and oid not in valid_objects_dict:
                                    raw_bbox = all_bboxes[oid]
                                    cat_name = vis_obj.get('category', raw_bbox.get('category', '')).lower().strip()

                                    native_min = raw_bbox.get('min')
                                    native_max = raw_bbox.get('max')

                                    if native_min is not None and native_max is not None:
                                        obj_min = np.array(native_min, dtype=float)
                                        obj_max = np.array(native_max, dtype=float)
                                    else:
                                        centroid = np.array(raw_bbox.get('centroid', [0.0, 0.0, 0.0]), dtype=float)
                                        axes = np.array(raw_bbox.get('axesLengths', [0.1, 0.1, 0.1]), dtype=float)
                                        obj_min = centroid - axes / 2.0
                                        obj_max = centroid + axes / 2.0

                                    valid_objects_dict[oid] = {{
                                        'id': oid,
                                        'category': cat_name,
                                        'min': obj_min,
                                        'max': obj_max
                                    }}

                    if not valid_objects_dict:
                        print(">>> [DEBUG] valid_objects_dict is EMPTY! No valid matched objects found.")
                        return []
                    else:
                        print(f">>> [DEBUG] Successfully loaded {{len(valid_objects_dict)}} valid visible objects.")

                    # --- STEP 3: LOGIC IMPLEMENTATION ---
                    # [YOUR CODE HERE]
                    # Choose TASK CATEGORY 1, 2, 3, 4, 5, 6, 7, 8, 9 or 10 based on the logical goal of the task.
                    # Ensure format_kwargs maps exactly to the parameters list!
                    # [WARNING] MAINTAIN EXACT INDENTATION (20 spaces) for the code you insert here.

                    return scene_qa_list

            if __name__ == "__main__":
                generator = {class_name}()
                generator.run()
        """).strip()

class ReviewerPrompts:
    @staticmethod
    def get_system_prompt():
        return textwrap.dedent("""
            # Role
            You are a Senior Logic Auditor specializing in 3D spatial Python code for the Holodeck QA framework.

            # AUDIT PROTOCOL (LOGIC GATES)

            1. **Task Intent Alignment (Crucial)**:
               - You must evaluate the code based on the provided "Task Meta".
               - **If Task asks for Distance/Proximity/Spatial relations**: The code MUST include mathematical distance/angle checks (e.g., `dist < 0.1` or `abs(d1 - d2)` or using vector Math).
               - **If Task asks for Counting/Existence**: The code MUST use `Counter` or calculate lengths of lists, and handle exact/boolean intent.
               - **If Task asks for Global Properties (e.g., room size)**: The code MUST extract directly from `scene_info.get(...)`. It MUST NOT compute sizes using object bounding boxes.

            2. **Syntax Check (Args & Namespaces)**:
               - `self.args` is an `argparse.Namespace` object.
               - **PASS**: Uses `getattr(self.args, 'key', default)`.
               - **FAIL**: Uses `self.args.get('key')` (this will cause runtime crashes).

            3. **Question Formatting**:
               - **PASS**: Dynamic template formatting using placeholders from the Task Meta.
               - **FAIL**: Explicitly embedding raw numbers/answers directly into the string assigned to `question`. (Numbers inside the `metadata` dict are strictly allowed).

            4. **Runtime Bounds & Logical Consistency (CRITICAL ANTI-BLINDSPOT)**:
               - You MUST mentally trace the data flow to ensure array indices and combinations are mathematically safe.
               - **FAIL (IndexError)**: The code accesses an index (e.g., `sorted_dists[1]`) but the preceding logic (e.g., `itertools.permutations(..., 2)`) only guarantees a list length of 1 for the candidates.
               - **FAIL (Logic Error)**: A "Comparison", "Closest", or "Farthest" task is generated, but the logic only extracts a SINGLE candidate to compare against a reference object. A comparison inherently requires multiple candidates.
               - **PASS**: The code dynamically ensures that the length of the lists/arrays strictly exceeds any hardcoded index calls, and dynamically validates that enough objects exist to fulfill the semantic intent of the question.

            # Output Format (MANDATORY STRICT JSON)
            You MUST return ONLY a raw JSON object.
            DO NOT wrap it in markdown code blocks (e.g., no ```json).
            DO NOT include any conversational text or preamble.

            Use this EXACT format:
            {
                "score": 100,
                "pass": true,
                "critical_issues": []
            }
        """).strip()

    @staticmethod
    def get_user_prompt(task_meta, generated_code):
        return textwrap.dedent(f"""
            # Task Meta (Target Intent)
            - Task Name: {task_meta.get('task_name', 'Unknown')}
            - Description: {task_meta.get('description', 'Unknown')}
            - Template: "{task_meta.get('question_template', 'Unknown')}"
            - Parameters: {task_meta.get('parameters', [])}

            # Code to Review
            ```python
            {generated_code}
            ```

            # Mandate
            Evaluate per the LOGIC GATES (Intent Alignment, Syntax/getattr, Formatting, Runtime Bounds).
            Ensure the code logic strictly fulfills the specific "Task Meta" above.
            **CRITICAL**: Trace the list lengths! If the code uses `list[1]`, verify that the preceding logic inherently guarantees at least 2 elements exist in that list.
            Return ONLY raw valid JSON with "score" (out of 100), "pass", and "critical_issues".
        """).strip()


class RefinerPrompts:
    @staticmethod
    def get_system_prompt():
        return textwrap.dedent("""
            # Role
            You are an Expert Python Developer specializing in refactoring generated multi-agent code.

            # CRITICAL STRUCTURAL REQUIREMENT (FULL SCRIPT LOCK)
            You MUST return the ENTIRE, fully functional Python script.
            Under NO circumstances may you abbreviate, truncate, or skip parts of the class.

            # CRITICAL BLACKLIST (FORBIDDEN ACTIONS)
            You will cause SILENT FAILURES if you violate these rules while repairing:
            ❌ DO NOT import or use `filter_valid_scene_objects`. Use manual list comprehensions instead.
            ❌ DO NOT import or use `is_distance_valid`. Use manual `abs(d1 - d2)` checks instead.
            ❌ DO NOT use `logger.info()`. ONLY use standard `print()` for debugging.
            ❌ DO NOT use `self.args.get()`. ALWAYS use `getattr(self.args, 'key', default)`.
            ❌ DO NOT do "LAZY FIXES" (e.g., bypassing an IndexError by simply adding `if len(arr) < x: continue`). This results in generating 0 items and completely FAILS the task.

            # REPAIR RULES
            1. **Syntax Fix**: Change any `.get()` on `self.args` to `getattr()`.
            2. **Validation Fix**: Add spatial math buffers (`< 0.1` etc.) for spatial tasks. Ensure `scene_info.get()` is used for global tasks.
            3. **Formatting Fix**: Remove hardcoded numeric answers from the `question` string.
            4. **Deep Logic Fix (ANTI-LAZY)**: If the Reviewer reports an `IndexError` or "Intent Alignment Failure" because a list only has 1 item, you MUST trace back and rewrite the UPSTREAM list generation logic.
               - *Example*: If the code needs multiple candidates but uses `itertools.permutations(..., 2)`, you MUST change it to `itertools.permutations(..., 4)` (or more) and slice it correctly (e.g., `target = combo[0]; candidates = combo[1:]`). DO NOT just ignore the error with a `continue` block.

            # Output
            Return the Full Python Script enclosed inside standard ```python ... ``` markdown blocks.
        """).strip()

    @staticmethod
    def get_user_prompt(task_meta, original_code, review_json):
        issues = review_json.get('critical_issues', [])
        issues_str = json.dumps(issues, indent=2) if issues else "[]"

        class_name = f"{task_meta['task_name'].title().replace('_', '')}QAGenerator"

        return textwrap.dedent(f"""
            # Issues to Fix (From Reviewer)
            {issues_str}

            # Task Meta
            - Task Name: {task_meta.get('task_name', 'Unknown')}
            - Template: "{task_meta.get('question_template', 'Unknown')}"

            # Mandate
            1. Refactor the code below to fix ONLY the CRITICAL LOGIC errors listed above.
            2. Remember the BLACKLIST: No forbidden functions, ALWAYS use getattr.
            3. **CRITICAL WARNING**: Do NOT just add `if len(...) < x: continue` to avoid IndexErrors. You MUST fix the root cause by ensuring the upstream logic (like permutations or combinations) actually extracts enough items to perform a valid comparison!
            4. **CRITICAL**: You must output the ENTIRE script. The code MUST end with this exact block:

            ```python
            if __name__ == "__main__":
                generator = {class_name}()
                generator.run()
            ```

            # Original Code
            ```python
            {original_code}
            ```

            Return the Full, corrected Code now.
        """).strip()
