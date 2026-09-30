import os
import sys
import json
import re
import cv2
import math
import numpy as np
from collections import defaultdict
from scipy.spatial.transform import Rotation as R

class CameraSkills:
    """
    [CameraSkills]
    High-level API library exposed to the LLM agent.
    Wraps AI2-THOR scene loading, bounding-box calculation, spatial validation, camera teleportation, and instance-segmentation parsing.
    """
    def __init__(self, controller):
        self.controller = controller
        self.scene_name = ""
        self.room_bounds = None
        self.room_center = [0.0, 0.0, 0.0]
        self.room_area = 0.0
        self.instance_bbox_dict = {}
        self.valid_object_map = {}
        self.category_counts = {}

    # ==========================================
    # 1. Scene and object initialization
    # ==========================================
    def load_scene(self, scene_name: str, scene_data: dict):
        self.scene_name = scene_name
        self.controller.reset(scene="Procedural")
        self.controller.step(action="CreateHouse", house=scene_data)

        if not self.controller.last_event.metadata["lastActionSuccess"]:
            raise RuntimeError(f"CreateHouse failed: {self.controller.last_event.metadata['errorMessage']}")

        self._parse_scene_objects(self.controller.last_event.metadata["objects"])
        return True

    def _parse_scene_objects(self, objects):
        self.instance_bbox_dict = {}
        self.valid_object_map = {}
        self.category_counts = {}
        auto_id_counters = defaultdict(int)
        pos_to_unique_id_map = {}

        ignored_types = {"Floor", "Wall", "Ceiling", "Room", "Structure"}
        room_blacklist = {
            "living room", "bedroom", "kitchen", "bathroom", "toilet",
            "dining room", "hallway", "office", "study", "laundry room",
            "garage", "balcony", "storage", "closet"
        }

        for obj in objects:
            if obj["objectType"] in ignored_types or "___" in obj["objectId"] or obj["name"].lower() in room_blacklist:
                continue

            clean_cat = self._get_clean_category_name(obj["name"])
            pos = obj["position"]
            pos_key = (clean_cat, round(pos["x"], 4), round(pos["y"], 4), round(pos["z"], 4))

            if pos_key in pos_to_unique_id_map:
                self.valid_object_map[obj["objectId"]] = pos_to_unique_id_map[pos_key]
                continue

            unique_key, cat_label = self._generate_unique_key(clean_cat, auto_id_counters)
            mapping_info = {"key": unique_key, "category": cat_label}
            pos_to_unique_id_map[pos_key] = mapping_info
            self.valid_object_map[obj["objectId"]] = mapping_info

            rot_y = obj["rotation"]["y"]
            normalized_axes = R.from_euler('y', -rot_y, degrees=True).as_matrix().flatten().tolist()
            true_center, true_size = self._get_precise_obb_data(obj, normalized_axes)

            if true_center is None: continue

            aabb_ref = obj.get("axisAlignedBoundingBox")
            if aabb_ref:
                c, s = aabb_ref["center"], aabb_ref["size"]
                ref_min = [c["x"] - s["x"]/2.0, c["y"] - s["y"]/2.0, c["z"] - s["z"]/2.0]
                ref_max = [c["x"] + s["x"]/2.0, c["y"] + s["y"]/2.0, c["z"] + s["z"]/2.0]
            else:
                ref_min = [true_center[0]-0.01, true_center[1]-0.01, true_center[2]-0.01]
                ref_max = [true_center[0]+0.01, true_center[1]+0.01, true_center[2]+0.01]

            self.instance_bbox_dict[unique_key] = {
                "name": unique_key,
                "category": cat_label,
                "centroid": true_center.tolist(),
                "axesLengths": true_size.tolist() if true_size is not None else [0,0,0],
                "min": ref_min,
                "max": ref_max,
                "max_dim": max(ref_max[0] - ref_min[0], ref_max[2] - ref_min[2])
            }
            self.category_counts[cat_label] = self.category_counts.get(cat_label, 0) + 1

        self.room_bounds, self.room_center, self.room_area = self._calculate_room_bounds()

    # ==========================================
    # 2. State queries
    # ==========================================
    def get_scene_metadata(self) -> dict:
        return {
            "dataset": "ai2thor_holodeck",
            "room_size": self.room_area,
            "room_center": self.room_center,
            "room_bounds": self.room_bounds,
            "object_counts": self.category_counts,
            "object_bboxes": {k: {
                "name": v["name"],
                "category": v["category"],
                "centroid": v["centroid"],
                "axesLengths": v["axesLengths"],
                "min": v["min"],
                "max": v["max"]
            } for k, v in self.instance_bbox_dict.items()}
        }

    def get_room_info(self):
        return {"bounds": self.room_bounds, "center": self.room_center, "area": self.room_area}

    def get_object_list(self, category_whitelist=None, category_blacklist=None):
        objects = []
        for unique_id, obj in self.instance_bbox_dict.items():
            cat = obj["category"]
            if category_whitelist and cat not in category_whitelist: continue
            if category_blacklist and cat in category_blacklist: continue

            obj_copy = obj.copy()
            obj_copy["id"] = unique_id
            objects.append(obj_copy)
        return objects

    # ==========================================
    # 3. Spatial trajectory planning
    # ==========================================
    def calculate_orbit_positions(self, cx: float, cz: float, base_radius: float, angles_deg: list) -> list:
        viewpoints = []
        for yaw in angles_deg:
            current_radius = base_radius
            min_radius = 0.5
            while current_radius >= min_radius:
                if yaw == 0:     tx, tz = cx, cz - current_radius
                elif yaw == 90:  tx, tz = cx - current_radius, cz
                elif yaw == 180: tx, tz = cx, cz + current_radius
                elif yaw == 270: tx, tz = cx + current_radius, cz
                else:
                    rad = math.radians(yaw - 90)
                    tx = cx + current_radius * math.cos(rad)
                    tz = cz + current_radius * math.sin(rad)

                if self._is_point_in_bounds(tx, tz, margin=0.1):
                    viewpoints.append({"yaw": yaw, "x": tx, "z": tz, "r": current_radius})
                    break
                current_radius -= 0.2
        return viewpoints

    # ==========================================
    # 4. Camera actions and visual parsing
    # ==========================================
    def capture_and_parse(self, x: float, y: float, z: float, yaw: float, pitch: float = 0.0, min_pixels: int = 300, dry_run: bool = False) -> dict:
        evt = self.controller.step(
            action="TeleportFull", x=x, y=y, z=z, rotation=dict(x=pitch, y=yaw, z=0),
            horizon=15.0, standing=True, forceAction=True
        )
        raw_meta = dict(evt.metadata)
        for heavy_key in ["frame", "instanceSegmentationFrame", "colorFrame", "depthFrame"]:
            raw_meta.pop(heavy_key, None)
        cam_pos = evt.metadata.get("cameraPosition", {"x": x, "y": y, "z": z})
        cam_x, cam_y, cam_z = cam_pos["x"], cam_pos["y"], cam_pos["z"]
        scene_bounds = evt.metadata.get("sceneBounds")
        if scene_bounds:
            sc_x, sc_y, sc_z = scene_bounds["center"]["x"], scene_bounds["center"]["y"], scene_bounds["center"]["z"]
            ss_x, ss_y, ss_z = scene_bounds["size"]["x"] / 2.0, scene_bounds["size"]["y"] / 2.0, scene_bounds["size"]["z"] / 2.0
            if not (sc_x - ss_x <= cam_x <= sc_x + ss_x and
                    sc_y - ss_y <= cam_y <= sc_y + ss_y and
                    sc_z - ss_z <= cam_z <= sc_z + ss_z):
                return {
                    "success": False,
                    "error_message": "Out of Bounds: Camera mathematical point is outside the room.",
                    "raw_metadata": raw_meta
                }
        for obj in evt.metadata.get("objects", []):
            bbox = obj.get("axisAlignedBoundingBox")
            if not bbox:
                continue
            if obj.get("objectType") in ["Room", "Floor", "Wall", "Ceiling", "Window", "Structure"]:
                continue

            bc_x, bc_y, bc_z = bbox["center"]["x"], bbox["center"]["y"], bbox["center"]["z"]
            bs_x, bs_y, bs_z = bbox["size"]["x"] / 2.0, bbox["size"]["y"] / 2.0, bbox["size"]["z"] / 2.0

            if (bc_x - bs_x <= cam_x <= bc_x + bs_x and
                bc_y - bs_y <= cam_y <= bc_y + bs_y and
                bc_z - bs_z <= cam_z <= bc_z + bs_z):
                return {
                    "success": False,
                    "error_message": f"Collision: Camera lens intersected inside solid object '{obj['name']}'.",
                    "raw_metadata": raw_meta
                }

        inst_frame = evt.instance_segmentation_frame
        reshaped_frame = inst_frame.reshape(-1, 3)
        unique_colors, counts = np.unique(reshaped_frame, axis=0, return_counts=True)
        color_counts = {tuple(c): count for c, count in zip(unique_colors, counts)}
        color_to_obj_id = evt.color_to_object_id

        aggregated_pixel_counts = defaultdict(int)
        key_to_category_map = {}

        for color_tuple, pixel_count in color_counts.items():
            if color_tuple in color_to_obj_id:
                unity_obj_id = color_to_obj_id[color_tuple]
                if unity_obj_id in self.valid_object_map:
                    record = self.valid_object_map[unity_obj_id]
                    unique_id = record["key"]
                    cat_name = record["category"]
                    if cat_name.lower() == "window": continue
                    aggregated_pixel_counts[unique_id] += pixel_count
                    key_to_category_map[unique_id] = cat_name

        visible_objects = []
        for unique_id, total_pixels in aggregated_pixel_counts.items():
            if total_pixels >= min_pixels:
                visible_objects.append({
                    "id": unique_id,
                    "category": key_to_category_map[unique_id],
                    "pixels": int(total_pixels)
                })

        if dry_run:
            return {"success": True, "rgb_frame": None}
        return {
            "success": True,
            "rgb_frame": evt.frame,
            "position": evt.metadata["agent"]["position"],
            "rotation": evt.metadata["agent"]["rotation"],
            "visible_objects": visible_objects
        }
    # ==========================================
    # 5. I/O helpers
    # ==========================================
    def save_image(self, rgb_frame, save_dir: str, filename: str) -> str:
        os.makedirs(save_dir, exist_ok=True)
        img_path = os.path.join(save_dir, f"{filename}.png")
        cv2.imwrite(img_path, cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR))
        return img_path

    def save_json(self, data_dict: dict, save_dir: str, filename: str) -> str:
        os.makedirs(save_dir, exist_ok=True)
        json_path = os.path.join(save_dir, f"{filename}.json")
        with open(json_path, "w") as f:
            json.dump(data_dict, f, indent=4)
        return json_path

    # ==========================================
    # Internal helper functions
    # ==========================================
    def _calculate_room_bounds(self):
        if not self.instance_bbox_dict:
            return None, [0,0,0], 0.0
        min_xs = [d['min'][0] for d in self.instance_bbox_dict.values()]
        max_xs = [d['max'][0] for d in self.instance_bbox_dict.values()]
        min_zs = [d['min'][2] for d in self.instance_bbox_dict.values()]
        max_zs = [d['max'][2] for d in self.instance_bbox_dict.values()]

        x_min, x_max = min(min_xs), max(max_xs)
        z_min, z_max = min(min_zs), max(max_zs)
        center = [(x_min + x_max)/2.0, 0.0, (z_min + z_max)/2.0]
        area = (x_max - x_min) * (z_max - z_min)
        return (x_min, x_max, z_min, z_max), center, area

    def _is_point_in_bounds(self, x, z, margin=0.0):
        if not self.room_bounds: return False
        x_min, x_max, z_min, z_max = self.room_bounds
        if x < (x_min + margin) or x > (x_max - margin): return False
        if z < (z_min + margin) or z > (z_max - margin): return False
        return True

    @staticmethod
    def _get_clean_category_name(unity_name):
        part1 = unity_name.split('|')[0].split('(')[0].strip()
        clean_base = re.sub(r'[-_]\d+$', '', part1).strip()
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', clean_base)
        return s1.replace(" ", "_").lower()

    @staticmethod
    def _generate_unique_key(base_snake, type_counters):
        current_count = type_counters[base_snake]
        type_counters[base_snake] += 1
        return f"{base_snake}-{current_count}", base_snake.replace("_", " ").strip()

    @staticmethod
    def _get_precise_obb_data(obj, rotation_matrix):
        # 1. Prefer the OBB, which is available for most furniture.
        obb = obj.get("objectOrientedBoundingBox")
        if obb and "cornerPoints" in obb:
            corners = np.array(obb["cornerPoints"])
            center = np.mean(corners, axis=0)
            R_mat = np.array(rotation_matrix).reshape(3, 3)
            size_x = np.max(corners @ R_mat[:, 0]) - np.min(corners @ R_mat[:, 0])
            size_y = np.max(corners @ R_mat[:, 1]) - np.min(corners @ R_mat[:, 1])
            size_z = np.max(corners @ R_mat[:, 2]) - np.min(corners @ R_mat[:, 2])
            return center, np.array([size_x, size_y, size_z])

        # 2. Fall back to the AABB for objects such as doors and windows.
        aabb = obj.get("axisAlignedBoundingBox")
        if aabb:
            center = np.array([aabb["center"]["x"], aabb["center"]["y"], aabb["center"]["z"]])
            world_size = np.array([aabb["size"]["x"], aabb["size"]["y"], aabb["size"]["z"]])

            # Use the rotation matrix to approximate local dimensions from world dimensions.
            R_mat = np.array(rotation_matrix).reshape(3, 3)
            local_size = np.abs(R_mat.T) @ world_size
            return center, local_size

        return None, None
