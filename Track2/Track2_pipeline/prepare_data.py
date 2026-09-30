"""Prepare Track 1 outputs for the Track 2 QA-generation pipeline."""

import argparse
import json
import shutil
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def infer_scene_name(bbox_path: Path) -> str:
    stem_name = bbox_path.name.removesuffix("_bbox.json")
    try:
        payload = load_json(bbox_path)
    except (OSError, json.JSONDecodeError):
        return stem_name
    if isinstance(payload, dict) and len(payload) == 1:
        first_key = next(iter(payload))
        if first_key.startswith("scene_"):
            return first_key
    for parent in bbox_path.parents:
        if parent.name.startswith("scene_"):
            return parent.name
    return stem_name


def choose_view_file(search_root: Path, scene_name: str) -> Path | None:
    candidates = [
        path
        for path in search_root.rglob("*_visible_views.json")
        if not path.name.startswith("schema_")
    ]
    if not candidates:
        return None
    exact = [path for path in candidates if path.name == f"{scene_name}_visible_views.json"]
    pool = exact or candidates
    return max(pool, key=lambda path: path.stat().st_size)


def copy_related_images(view_path: Path, destination: Path) -> int:
    copied = 0
    try:
        view_data = load_json(view_path)
    except (OSError, json.JSONDecodeError):
        return copied

    image_names = set()

    def collect(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "image_path" and isinstance(child, str):
                    image_names.add(Path(child).name)
                else:
                    collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(view_data)
    for image_name in image_names:
        matches = list(view_path.parent.rglob(image_name))
        if matches:
            shutil.copy2(matches[0], destination / image_name)
            copied += 1
    return copied


def prepare_scene(bbox_path: Path, source_root: Path, output_root: Path) -> tuple[str, int]:
    scene_name = infer_scene_name(bbox_path)
    scene_search_root = bbox_path.parent
    if scene_search_root == source_root:
        matching_dirs = [path for path in source_root.rglob(scene_name) if path.is_dir()]
        if matching_dirs:
            scene_search_root = matching_dirs[0]

    destination = output_root / scene_name
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bbox_path, destination / f"{scene_name}_bbox.json")

    view_path = choose_view_file(scene_search_root, scene_name)
    image_count = 0
    if view_path is not None:
        shutil.copy2(view_path, destination / f"{scene_name}_visible_views.json")
        image_count = copy_related_images(view_path, destination)
    else:
        print(f"[Warning] No visible-view JSON found for {scene_name}.")

    return scene_name, image_count


def main():
    script_dir = Path(__file__).resolve().parent
    repository_root = script_dir.parents[1]
    default_source = repository_root / "Track1" / "data" / "collected"
    default_output = script_dir / "data"

    parser = argparse.ArgumentParser(
        description="Copy and normalize Track 1 metadata for Track 2."
    )
    parser.add_argument("--source", type=Path, default=default_source)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument(
        "--task-key",
        help="Optionally restrict discovery to a Track 1 task directory such as A.",
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Track 1 output directory does not exist: {source}")

    search_root = source
    if args.task_key:
        matches = [path for path in source.rglob(args.task_key) if path.is_dir()]
        if not matches:
            raise FileNotFoundError(
                f"No task directory named '{args.task_key}' was found under {source}"
            )

    bbox_files = [
        path
        for path in search_root.rglob("*_bbox.json")
        if not path.name.startswith("schema_")
    ]
    if args.task_key:
        bbox_files = [path for path in bbox_files if args.task_key in path.parts]
    if not bbox_files:
        raise FileNotFoundError(f"No Track 1 *_bbox.json files were found under {source}")

    selected = {}
    for bbox_path in bbox_files:
        scene_name = infer_scene_name(bbox_path)
        current = selected.get(scene_name)
        if current is None or bbox_path.stat().st_size > current.stat().st_size:
            selected[scene_name] = bbox_path

    output.mkdir(parents=True, exist_ok=True)
    for scene_name, bbox_path in sorted(selected.items()):
        prepared_scene, image_count = prepare_scene(bbox_path, source, output)
        print(f"[Prepared] {prepared_scene}: metadata and {image_count} referenced image(s)")

    print(f"Prepared {len(selected)} scene(s) in {output}")


if __name__ == "__main__":
    main()
