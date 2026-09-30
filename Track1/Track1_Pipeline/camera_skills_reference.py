"""English API reference injected into Track 1 camera-agent prompts."""

import textwrap


CAMERA_SKILLS_INTERFACE_STR = textwrap.dedent(
    '''
class CameraSkills:
    """High-level API exposed to the camera agent.

    The implementation deduplicates overlapping Holodeck object IDs and wraps
    scene loading, spatial validation, camera teleportation, image capture, and
    instance-segmentation parsing.
    """

    def load_scene(self, scene_name: str, scene_data: dict) -> bool:
        """Load a scene and parse deduplicated object boxes and room bounds.

        Args:
            scene_name: Scene identifier.
            scene_data: Holodeck-compatible scene JSON object.

        Returns:
            True when the scene loads successfully.
        """
        pass

    def get_scene_metadata(self) -> dict:
        """Return global metadata with clean, unique object IDs.

        Call this before image collection and save its result as
        ``<scene_name>_bbox.json``. The returned dictionary contains dataset,
        room_size, room_center, room_bounds, object_counts, and object_bboxes.
        Every object_bboxes entry provides name, category, centroid,
        axesLengths, min, and max.
        """
        pass

    def get_room_info(self) -> dict:
        """Return room bounds, center, and area."""
        pass

    def get_object_list(self, category_whitelist=None, category_blacklist=None) -> list:
        """Return filtered objects with unique IDs and geometric attributes.

        Each result contains id, category, centroid, min, max, and max_dim.
        """
        pass

    def calculate_orbit_positions(
        self,
        cx: float,
        cz: float,
        base_radius: float,
        angles_deg: list,
    ) -> list:
        """Return valid orbit viewpoints and shrink the radius when needed.

        A requested angle is omitted if no in-bounds point can be found.
        Each result contains yaw, x, z, and the final radius r.
        """
        pass

    def capture_and_parse(
        self,
        x: float,
        y: float,
        z: float,
        yaw: float,
        pitch: float = 0.0,
        min_pixels: int = 300,
    ) -> dict:
        """Teleport the camera, capture RGB, and parse visible instances.

        A successful result contains success, rgb_frame, position, rotation,
        and visible_objects. Each visible object has id, category, and pixels.
        Positive pitch values look downward.
        """
        pass

    def save_image(self, rgb_frame, save_dir: str, filename: str) -> str:
        """Save an RGB frame as ``<filename>.png`` and return its path."""
        pass

    def save_json(self, data_dict: dict, save_dir: str, filename: str) -> str:
        """Save a dictionary as ``<filename>.json`` and return its path."""
        pass
'''
)
