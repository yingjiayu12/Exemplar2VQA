import math
import numpy as np
from collections import Counter
from utils.common_utils import cal_3d_bbox_distance_between_categories

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
    rad = np.radians(float(angle_deg))
    fwd_x = np.sin(rad)
    fwd_z = np.cos(rad)
    fwd_vec = np.array([fwd_x, fwd_z])
    right_x = np.cos(rad)
    right_z = -np.sin(rad)
    right_vec = np.array([right_x, right_z])
    fwd_vec = fwd_vec / (np.linalg.norm(fwd_vec) + 1e-6)
    right_vec = right_vec / (np.linalg.norm(right_vec) + 1e-6)
    return right_vec, fwd_vec

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
    corners = [
        np.array([min_xz[0], min_xz[1]]), # min_x, min_z
        np.array([min_xz[0], max_xz[1]]), # min_x, max_z
        np.array([max_xz[0], min_xz[1]]), # max_x, min_z
        np.array([max_xz[0], max_xz[1]])  # max_x, max_z
    ]
    projections = [np.dot(c, axis_vec) for c in corners]
    return min(projections), max(projections)

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
    r_l_min, r_l_max = ref_projs['right_axis']
    r_d_min, r_d_max = ref_projs['fwd_axis']
    t_l_min, t_l_max = target_projs['right_axis']
    t_d_min, t_d_max = target_projs['fwd_axis']
    is_hit = False
    if direction == "left":
        if t_l_max < r_l_min - threshold:
            is_hit = True      
    elif direction == "right":
        if t_l_min > r_l_max + threshold:
            is_hit = True
    elif direction == "front":
        if t_d_min > r_d_max + threshold:
            is_hit = True
    elif direction == "behind":
        if t_d_max < r_d_min - threshold:
            is_hit = True
    return is_hit

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
    center = np.asarray(obj_data["centroid"], dtype=np.float64).reshape(3)
    if include_corners:
        rotation = np.asarray(
            obj_data["normalizedAxes"], dtype=np.float64
        ).reshape(3, 3).T
        half_extent = np.asarray(
            obj_data["axesLengths"], dtype=np.float64
        ).reshape(3) / 2.0
        signs = np.array(
            [
                [-1, -1, -1],
                [-1, -1, 1],
                [-1, 1, -1],
                [-1, 1, 1],
                [1, -1, -1],
                [1, -1, 1],
                [1, 1, -1],
                [1, 1, 1],
            ],
            dtype=np.float64,
        )
        local_corners = signs * half_extent
        vertices = local_corners @ rotation.T + center
        points_3d = np.concatenate([center.reshape(1, 3), vertices], axis=0)
    else:
        points_3d = center.reshape(1, 3)
    return points_3d[:, [0, 2]]


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
    if blacklist_set is None:
        blacklist_set = {
            "window", "wall", "ceiling", "floor", "curtain", 
            "structure", "room", "unknown", "object", "doorframe", 
            "pillow", "blanket", "mirror", "door", "coffee mug", "book"
        }
    global_obj_map = {}
    all_categories = []
    for bbox_key, data in object_bboxes.items():
        min_coord = np.array(data.get("min", []))
        max_coord = np.array(data.get("max", []))
        cat = data.get("category")
        if len(min_coord) == 3 and len(max_coord) == 3 and cat:
            cat_clean = cat.lower().strip()
            if any(b_item in cat_clean for b_item in blacklist_set):
                continue
            if cat_clean not in whitelist_set:
                continue
            center_x = (min_coord[0] + max_coord[0]) / 2.0
            center_z = (min_coord[2] + max_coord[2]) / 2.0
            global_obj_map[bbox_key] = {
                "id": bbox_key,
                "category": cat_clean,
                "center_xz": np.array([center_x, center_z])
            }
            all_categories.append(cat_clean)
    return global_obj_map, Counter(all_categories)

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
    v1 = np.tile(vec_ref, (vec_targets.shape[0], 1))
    v2s = vec_targets
    dot_products = (v1 * v2s).sum(axis=1)
    mag_v1 = np.linalg.norm(v1, axis=1)
    mag_v2s = np.linalg.norm(v2s, axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        cos_vals = dot_products / (mag_v1 * mag_v2s + 1e-8)
        cos_vals = np.clip(cos_vals, -1.0, 1.0)
        angles = np.arccos(cos_vals)
    crs_products = v1[:, 0] * v2s[:, 1] - v1[:, 1] * v2s[:, 0]
    angles = np.where(crs_products >= 0., angles, 2 * math.pi - angles)
    return np.degrees(angles)


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
    vec_cam_to_obj = target_pos_xz - cam_pos_xz
    rad = np.radians(float(heading_angle_deg))
    move_vec = np.array([np.sin(rad), np.cos(rad)]) 
    move_vec = move_vec / (np.linalg.norm(move_vec) + 1e-6)
    return np.dot(vec_cam_to_obj, move_vec)

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
    pairs = [
        (triple_cats[0], triple_cats[1]),
        (triple_cats[0], triple_cats[2]),
        (triple_cats[1], triple_cats[2])
    ]
    for cat1, cat2 in pairs:
        if (cat1, cat2) in dist_lookup:
            dist = dist_lookup[(cat1, cat2)]
        elif (cat2, cat1) in dist_lookup:
            dist = dist_lookup[(cat2, cat1)]
        else:
            obj1 = valid_objects_map[cat1]
            obj2 = valid_objects_map[cat2]
            dist = cal_3d_bbox_distance_between_categories([obj1], [obj2])
            dist_lookup[(cat1, cat2)] = dist
            dist_lookup[(cat2, cat1)] = dist

        if dist < min_dist or dist > max_dist:
            return False
    return True


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
    quadrants = (angles // 90).astype(int)
    if (quadrants[1:] != quadrants[0]).sum() > 2:
        return True
    remainder = angles[0] % 90
    if (90 - remainder) < threshold:
        return True
    return False

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
    if angle_deg >= 270: return "front-right"
    elif angle_deg >= 180: return "back-right"
    elif angle_deg >= 90: return "back-left"
    else: return "front-left"

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
                2: {...},               # Corresponds to angle "180"
                3: {...}                # Corresponds to angle "270"
            }
            Returns an empty dict if required angles are missing.
    """
    if blacklist_set is None:
        blacklist_set = {
            "window", "wall", "ceiling", "floor", "curtain", 
            "structure", "room", "unknown", "object", "doorframe", 
            "pillow", "blanket", "mirror", "door", "coffee mug", "book"
        }
    views = visible_views_data.get("views", {})
    angle_keys = ["0", "90", "180", "270"]
    for k in angle_keys:
        if k not in views:
            return {}
    view_categories_map = {}
    for idx, angle in enumerate(angle_keys):
        obj_list = views[angle].get("visible_objects", [])
        categories_in_view = set()
        for obj in obj_list:
            cat = obj.get("category", "").lower().strip()
            if any(b_item in cat for b_item in blacklist_set):
                continue
            if cat in whitelist_set:
                categories_in_view.add(cat.capitalize())
        view_categories_map[idx] = categories_in_view
    return view_categories_map


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
    rot_str = rotation_desc.lower()
    rot_delta = 0
    if "180" in rot_str or "around" in rot_str:
        rot_delta = 2
    elif "90" in rot_str:
        if "left" in rot_str:
            rot_delta = -1
        elif "right" in rot_str:
            rot_delta = 1
    look_str = look_direction.lower()
    look_delta = 0
    if "left" in look_str:
        look_delta = -1
    elif "right" in look_str:
        look_delta = 1
    elif "back" in look_str or "behind" in look_str:
        look_delta = 2
    final_idx = (start_view_idx + rot_delta + look_delta) % 4
    return final_idx