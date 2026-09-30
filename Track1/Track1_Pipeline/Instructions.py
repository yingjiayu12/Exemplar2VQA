"""Natural-language camera collection instructions used by Track 1."""

import textwrap


class CameraInstructions:
    """Registry of camera collection tasks keyed by short identifiers."""

    TASKS = {
        "A": textwrap.dedent(
            """
            Please execute the following data-collection task:
            1. Before taking any photos, extract the current scene's global metadata, including deduplicated object bounding boxes, and save it as <scene_name>_bbox.json.
            2. Find object instances in the room.
            3. For each selected object, take four photos from a radius of 1.5 meters at 0, 90, 180, and 270 degrees around its center.
            4. Set the camera height to 1.65 meters and pitch it downward by 15 degrees so that the entire object remains in frame.
            5. If any viewpoint is unreachable, for example because the object is against a wall, discard that object. Keep only objects for which all four images are captured successfully.
            6. Aggregate the successful multi-view records into a visible-views JSON file.
            7. Stop after collecting two objects that satisfy all constraints.
            """
        ).strip(),
    }

    @classmethod
    def get_instruction(cls, task_key: str) -> str:
        if task_key not in cls.TASKS:
            raise KeyError(
                f"Task key '{task_key}' not found in Instructions.py. "
                f"Available keys: {list(cls.TASKS.keys())}"
            )
        return cls.TASKS[task_key]
