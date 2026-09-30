import os
import json
import glob
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys
sys.path.append(str(Path(__file__).parent))
from utils.vsibench_utils import vsibench_doc_to_text, MCA_QUESTION_TYPES, NA_QUESTION_TYPES

# Constants for conversation roles
HUMAN_ROLE = "human"
GPT_ROLE = "gpt"
DEFAULT_DATASET_NAME = "unknown_dataset"

def format_qa(qa: Dict[str, Any]) -> List[Dict[str, str]]:
    """Formats a question-answer dictionary into a conversation structure."""
    question_type = qa.get("question_type", "unknown")

    question = vsibench_doc_to_text(qa)
    # Add image token to the question
    question = "<image>\n" + question

    if question_type in MCA_QUESTION_TYPES:
        answer = qa.get('mc_answer', '') # Use .get for robustness
        if not answer:
            answer = qa.get('answer', '')
    elif question_type in NA_QUESTION_TYPES:
        answer = qa.get('ground_truth', '') # Use .get for robustness
        if not answer:
            answer = qa.get('answer', '')
    else:
        # Log a warning or handle unknown types appropriately
        print(f"Warning: Unknown question type encountered: {question_type}")
        answer = qa.get('answer', '')

    conversations = [
            {
                "from": HUMAN_ROLE,
                "value": question
            },
            {
                "from": GPT_ROLE,
                "value": str(answer)
            }
        ]
    return conversations


# Removed get_scene_name function as it is no longer needed
# def get_scene_name(video_path_str: Optional[str], dataset_name: Optional[str] = None) -> str:
#     """
#     Extracts the scene name from the video path based on the dataset.
#     ... (rest of the function code) ...
#     """
#     ... (function body) ...


def gen_conversation(qa: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a conversation dictionary from a QA item."""
    conversation = dict()
    conversation["id"] = str(uuid.uuid4()) # Unique ID for each conversation

    video_path_str = qa.get("video_path", "")
    dataset_name = qa.get("dataset", DEFAULT_DATASET_NAME)
    conversation["data_source"] = dataset_name
    scene_name_val = qa.get("scene_name", "") # Renamed to avoid conflict
    conversation["scene_name"] = scene_name_val
    conversation["question_type"] = qa.get("question_type", "")
    # Directly use the video path from the input QA data
    conversation["video"] = video_path_str # Removed
    # scene_name = get_scene_name(video_path_str, dataset_name) # Removed
    # Construct the new video path using a template
    # if scene_name_val:
    #     new_video_path = VIDEO_DIR_TEMPLATE.format(dataset_name=dataset_name, scene_name=scene_name_val)
    # else:
    #     # Handle cases where scene name could not be determined
    #     print(f"Warning: Could not determine scene name for video path: {video_path_str}. Setting video path to empty.")
    #     new_video_path = ""
    # conversation["video"] = new_video_path

    conversation["conversations"] = format_qa(qa)
    return conversation


def process_qa_files(input_path_str: str, output_path_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """Processes QA JSON file(s) from an input path (file or directory) into a single list."""
    input_path = Path(input_path_str)
    json_files: List[Path] = []

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path_str}")

    if input_path.is_file():
        if input_path.suffix.lower() == ".json":
            json_files = [input_path]
        else:
            raise ValueError(f"Input file must be a JSON file, but got: {input_path_str}")
    elif input_path.is_dir():
        json_files = list(input_path.glob("*.json"))
        if not json_files:
            print(f"Warning: No JSON files found in directory {input_path_str}")
            return []
    else:
        # This case handles other file system objects that are not files or directories
        raise ValueError(f"Input path is not a valid file or directory: {input_path_str}")

    all_qa_list: List[Dict[str, Any]] = []
    
    # Read and merge all json files
    for json_path in json_files:
        try:
            with open(json_path, "r", encoding='utf-8') as f: # Specify encoding
                qa_list = json.load(f)
                if isinstance(qa_list, list): # Ensure loaded data is a list
                     all_qa_list.extend(qa_list)
                else:
                     print(f"Warning: Expected a list in {json_path}, but got {type(qa_list)}. Skipping.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {json_path}. Skipping.")
        except Exception as e:
            print(f"Error reading file {json_path}: {e}. Skipping.")

    # Update IDs sequentially and count task types
    task_type_counts: Dict[str, int] = {}
    processed_qa_list: List[Dict[str, Any]] = []
    for idx, qa in enumerate(all_qa_list):
        qa["id"] = idx # Assign sequential ID

        task_type = qa.get("question_type", "unknown")
        # Normalize object_rel_direction types
        # Commented out as OBJECT_REL_DIRECTION_PREFIX is not defined in this scope
        # if task_type.startswith(OBJECT_REL_DIRECTION_PREFIX):
        #     task_type = OBJECT_REL_DIRECTION_PREFIX
        #     qa["question_type"] = task_type # Update the qa dict as well

        task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
        processed_qa_list.append(qa)
    
    # Print statistics
    total_pairs = len(processed_qa_list)
    print(f"Total number of QA pairs processed: {total_pairs}")
    if total_pairs > 0:
        print("Number of tasks by type:")
        for task_type, count in sorted(task_type_counts.items()): # Sort for consistent output
            print(f"  {task_type}: {count}")

    # Generate conversations
    conversations = [gen_conversation(qa) for qa in processed_qa_list]

    # Save conversations
    if output_path_str:
        output_dir = Path(output_path_str).parent
        output_dir.mkdir(parents=True, exist_ok=True) # Create output dir if not exists
        try:
            with open(output_path_str, "w", encoding='utf-8') as f: # Specify encoding
                json.dump(conversations, f, indent=2)
            print(f"Merged QA data saved to {output_path_str}")
        except IOError as e:
            print(f"Error writing output file {output_path_str}: {e}")
        except Exception as e:
             print(f"An unexpected error occurred during saving: {e}")

    return conversations

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Format QA JSON file(s) into conversations format.")
    parser.add_argument("--input_path", type=str, required=True, help="Path to input JSON file or directory containing JSON files")
    parser.add_argument("--output_path", type=str, required=True, help="Output file path for formatted QA pairs (JSON)")
    
    args = parser.parse_args()
    
    # Define OBJECT_REL_DIRECTION_PREFIX if it's used and not defined/imported
    # Example: OBJECT_REL_DIRECTION_PREFIX = "object_rel_direction"
    # This needs clarification based on where OBJECT_REL_DIRECTION_PREFIX is expected from.
    # If it's not used or defined, the related block in merge_qa_files should be adjusted/removed.
    # OBJECT_REL_DIRECTION_PREFIX = "object_rel_direction" # Example definition, uncomment and set if needed

    try:
        process_qa_files(args.input_path, args.output_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
