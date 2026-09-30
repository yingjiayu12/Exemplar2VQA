import json
import os
import glob

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.abspath(
    os.environ.get("EXEMPLAR2VQA_DATA_ROOT", os.path.join(PIPELINE_DIR, "data"))
)
TARGET_FILES = ["*_bbox.json", "*_visible_views.json"]

def analyze_value_type(value):
    """Return a compact description of a JSON value type."""
    if isinstance(value, str):
        return "<str>"
    elif isinstance(value, bool):
        return "<bool>"
    elif isinstance(value, int):
        return "<int>"
    elif isinstance(value, float):
        return "<float>"
    elif value is None:
        return "<null>"
    else:
        return "<unknown>"

def is_homogeneous(data_dict):
    if not data_dict:
        return True
    iterator = iter(data_dict.values())
    try:
        first_val = next(iterator)
    except StopIteration:
        return True
    first_type = type(first_val)
    for val in iterator:
        if type(val) != first_type:
            return False
    return True

def generate_compact_schema(data, key_threshold=4):
    """Recursively generate a compact schema."""
    if isinstance(data, dict):
        if not data:
            return {}
        
        keys = list(data.keys())
        is_large_collection = (len(keys) > key_threshold) and is_homogeneous(data)
        
        if is_large_collection:
            sample_key = keys[0]
            sample_val = data[sample_key]
            key_desc = f"<{sample_key} (Example Key)>"
            return {
                key_desc: generate_compact_schema(sample_val),
                "__NOTE__": f"<... This dict contains {len(keys)} items of the same type (keys are dynamic IDs/Names) ...>"
            }
        
        schema = {}
        for k, v in data.items():
            schema[k] = generate_compact_schema(v)
        return schema

    elif isinstance(data, list):
        if not data:
            return []
        
        sample_item = generate_compact_schema(data[0])
        
        if len(data) <= 4 and all(isinstance(x, (int, float)) for x in data):
             return [analyze_value_type(x) for x in data]
        else:
            return [
                sample_item,
                f"<... List containing {len(data)} items ...>"
            ]
    else:
        return analyze_value_type(data)

def process_single_file(file_path):
    filename = os.path.basename(file_path)
    if filename.startswith("schema_"):
        return False
    
    dir_name = os.path.dirname(file_path)
    output_name = f"schema_{filename}"
    output_path = os.path.join(dir_name, output_name)
    
    print(f"Processing: {filename} ...", end=" ")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        schema = generate_compact_schema(content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        
        print(f"[Done] -> Saved schema.")
        return True
    except Exception as e:
        print(f"\n[Error] Failed: {e}")
        return False

def main():
    print(f"=== Starting FIXED Schema Extraction ===")
    
    if not os.path.exists(DATA_ROOT):
        print(f"[Fatal Error] Path not found: {DATA_ROOT}")
        return

    count = 0
    for root, dirs, files in os.walk(DATA_ROOT):
        for pattern in TARGET_FILES:
            for file_path in glob.glob(os.path.join(root, pattern)):
                if process_single_file(file_path):
                    count += 1
    
    print(f"\n=== Complete. Processed {count} files. ===")

if __name__ == "__main__":
    main()