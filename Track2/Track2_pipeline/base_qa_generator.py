import os
import json
import argparse
import tqdm
import random
import glob
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
import logging
import numpy as np

import question_templates as prompt_templates

logger = logging.getLogger(__name__)

class BaseQAGenerator(ABC):
    """
    Base class for generating QA pairs.
    
    """
    def __init__(self):
        self.args = self._parse_args()
        
        # 1. Validate the data root.
        assert self.args.processed_data_path is not None, "processed_data_path must be provided"
        if not os.path.exists(self.args.processed_data_path):
            raise FileNotFoundError(f"Data root not found: {self.args.processed_data_path}")
        self.base_processed_path = self.args.processed_data_path

        logger.info(f"Data Root: {self.base_processed_path}")
        logger.info(f"Dataset Name: {self.args.dataset}")
        logger.info("Scanning directory for scenes...")

        self.scene_list = []
        
        all_items = os.listdir(self.base_processed_path)
        
        if self.args.dataset == 'holodeck':
            # Layout: root/scene_0/a_living_room_bbox.json
            for item in all_items:
                item_path = os.path.join(self.base_processed_path, item)
                if not os.path.isdir(item_path):
                    continue
                
                bbox_files = [
                    path
                    for path in glob.glob(os.path.join(item_path, "*_bbox.json"))
                    if not os.path.basename(path).startswith("schema_")
                ]
                if bbox_files:
                    self.scene_list.append(item)  # For example, scene_0.
        else:
            # Layout: root/scene0000_00/scannet_format_meta.json
            for item in all_items:
                item_path = os.path.join(self.base_processed_path, item)
                
                if not os.path.isdir(item_path):
                    continue
                    
                meta_path = os.path.join(item_path, "scannet_format_meta.json")
                if os.path.exists(meta_path):
                    self.scene_list.append(item)
        
        self.scene_list.sort()

        if not self.scene_list:
            logger.error(f"No valid scenes found in {self.base_processed_path}!")
            if self.args.dataset == 'holodeck':
                logger.error("Make sure your Holodeck folders contain '*_bbox.json'.")
            else:
                logger.error("Make sure your Scannet folders contain 'scannet_format_meta.json'.")
        else:
            logger.info(f"Found {len(self.scene_list)} valid scenes to process.")

        self.question_template = None if self.args.question_template is None else getattr(prompt_templates, self.args.question_template)
        self.all_qa_list = []
        self.answer_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        self.option_letters = ['A', 'B', 'C', 'D']

    def _load_json(self, file_path):
        """Helper to safely load JSON."""
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON {file_path}: {e}")
            return None

    def _identify_unique_instances(self, scene_name, scene_info, vertex_data=None):
        """
        Modified to rely ONLY on metadata (object_counts).
        """
        object_counts = scene_info.get('object_counts', {})
        object_bboxes = scene_info.get('object_bboxes', {})
        
        if not object_counts or not object_bboxes:
            logger.warning(f"Scene {scene_name}: Missing counts or bboxes in metadata.")
            return []

        unique_category_instance_info = []
        
        for category_name, count in object_counts.items():
            if count == 1:
                if category_name not in object_bboxes or not object_bboxes[category_name]:
                    continue
                try:
                    instance_details = object_bboxes[category_name][0]
                    instance_id = instance_details.get('instance_id')
                    
                    if instance_id is not None:
                        unique_category_instance_info.append({
                            "instance_id": int(instance_id),
                            "category_name": category_name
                        })
                except Exception as e:
                    logger.warning(f"Scene {scene_name}: Error processing category {category_name}: {e}")
                    continue
        
        return unique_category_instance_info

    @abstractmethod
    def get_default_args(self):
        pass

    @abstractmethod
    def generate_scene_qa(self, scene_name, scene_info, frame_info_for_scene):
        pass

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='Base QA Generator')
        
        parser.add_argument('--split_path', type=str, help='(Ignored) Path to scene list json.')
        parser.add_argument('--split_type', type=str, default='all', help='(Optional) Tag for output file.')
        
        parser.add_argument('--processed_data_path', type=str, required=True, help='Root path to dataset.')
        parser.add_argument('--output_dir', type=str, default='./output', help='Output directory.')
        parser.add_argument('--dataset', type=str, default='scannet', help='Dataset name.')
        
        parser.add_argument('--question_template', type=str)
        parser.add_argument('--num_subsample', type=int, default=6)
        parser.add_argument('--question_type', type=str)
        parser.add_argument('--output_filename_prefix', type=str)
        parser.add_argument('--num_workers', type=int, default=1)

        # Load defaults from subclass
        temp_instance = self.__class__.__new__(self.__class__)
        default_args = temp_instance.get_default_args()
        parser.set_defaults(**default_args)
        
        return parser.parse_args()

    def _process_scene(self, scene_name):
        scene_name = scene_name.strip()
        
        scene_dir = os.path.join(self.base_processed_path, scene_name)

        if self.args.dataset == 'holodeck':
            bbox_files = glob.glob(os.path.join(scene_dir, "*_bbox.json"))
            if not bbox_files:
                logger.warning(f"Scene {scene_name}: No *_bbox.json found, skipping.")
                return [], Counter()
            meta_path = bbox_files[0]
        else:
            meta_path = os.path.join(scene_dir, "scannet_format_meta.json")
        
        full_meta = self._load_json(meta_path)
        if not full_meta:
            return [], Counter()

        scene_info = full_meta.get(scene_name, full_meta)

        # Build paths to scene data.
        frame_dirs = {
            "depth_dir": os.path.join(scene_dir, "depth_map"),
            "extrinsic_dir": os.path.join(scene_dir, "extrinsic"),
            "intrinsic_dir": os.path.join(scene_dir, "intrinsic"),
            "point_map_dir": os.path.join(scene_dir, "point_map"),
            "scene_path": scene_dir
        }
        
        if not scene_info.get('object_counts'):
            logger.warning(f"Scene {scene_name}: 'object_counts' missing/empty. Skipping.")
            return [], Counter()

        local_answer_counts = Counter()
        try:
            scene_qa_list = self.generate_scene_qa(scene_name, scene_info, frame_dirs)
        except Exception as e:
            logger.error(f"Error generating QA for {scene_name}: {e}", exc_info=True)
            return [], Counter()

        if scene_qa_list and len(scene_qa_list) > self.args.num_subsample:
            scene_qa_list = random.sample(scene_qa_list, self.args.num_subsample)

        for qa in scene_qa_list:
            if 'mc_answer' in qa:
                ans = str(qa['mc_answer'])
                if ans in self.option_letters:
                    local_answer_counts[ans] += 1
                else:
                    local_answer_counts[ans] += 1

        return scene_qa_list, local_answer_counts

    def run(self):
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        if not self.scene_list:
             logger.error("No valid scenes found to process. Exiting.")
             return

        results_map = {}
        total_answer_counts = Counter()
        
        num_workers = max(1, self.args.num_workers)
        logger.info(f"Starting parallel processing with {num_workers} workers...")

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(self._process_scene, s): s for s in self.scene_list}

            for future in tqdm.tqdm(as_completed(futures), total=len(self.scene_list), desc="Generating"):
                scene_name = futures[future]
                try:
                    qas, counts = future.result()
                    results_map[scene_name] = qas
                    total_answer_counts.update(counts)
                except Exception as e:
                    logger.error(f"Worker exception for {scene_name}: {e}")

        aggregated_results = []
        
        for scene_name in self.scene_list:
            if scene_name in results_map and results_map[scene_name]:
                aggregated_results.extend(results_map[scene_name])

        logger.info("Assigning global IDs...")
        for i, qa in enumerate(aggregated_results):
            qa["id"] = i

        self.all_qa_list = aggregated_results
        self.answer_counts = dict(sorted(total_answer_counts.items()))

        logger.info(f"Generated {len(self.all_qa_list)} QA pairs.")
        logger.info(f"Distribution: {self.answer_counts}")
        
        self._save_results()

    def _save_results(self):
        output_filename = f"{self.args.output_filename_prefix}_{self.args.dataset}.json"
        save_path = os.path.join(self.args.output_dir, output_filename)
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try:
            with open(save_path, "w") as f:
                json.dump(self.all_qa_list, f, indent=4)
            logger.info(f"Saved results to: {save_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
