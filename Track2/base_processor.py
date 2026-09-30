import argparse
import os
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, TypeVar, Generic
from multiprocessing import Pool, cpu_count
import tqdm
import random
import numpy as np
from shapely.geometry.polygon import Polygon

# Basic logging setup - gets configured once when the main script runs
# Avoid basicConfig here if it might be called multiple times by different modules.
# Rely on the main script entry point (__main__) to configure logging.
logger = logging.getLogger(__name__)

TConfig = TypeVar('TConfig', bound='BaseProcessorConfig')

@dataclass
class BaseProcessorConfig:
    """Base configuration for scene processing."""
    save_dir: str = "output"
    output_filename: str = "metadata.json"
    num_workers: int = 1
    overwrite: bool = False
    random_seed: int = 42
    scene_list_file: str = "" # Should be set by subclasses or arguments
    split: str = "" # Should be set by subclasses or arguments
    dataset_name: str = "" # Should be set by subclasses or arguments

def json_converter(obj):
    """Custom JSON converter to handle non-serializable types like numpy arrays/numbers and shapely Polygons."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist() # Convert numpy arrays to lists
    elif isinstance(obj, Polygon):
        logger.warning("Found Shapely Polygon object during JSON serialization. Converting to its WKT string representation.")
        return obj.wkt # Convert Polygon to Well-Known Text string, or handle differently
    elif isinstance(obj, bytes):
        return obj.decode('utf-8') # Decode bytes to string if encountered
    # Let the default encoder raise the error for other types
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class AbstractSceneProcessor(ABC, Generic[TConfig]):
    """Abstract base class for processing multiple scenes, often in parallel."""
    def __init__(self, config: TConfig):
        """
        Initializes the processor with configuration and sets up seed.
        Logging should be configured externally before instantiation.
        """
        self.config = config
        self._setup_seed()
        logger.info(f"Initialized processor with config: {self.config}")

    def _setup_seed(self):
        """Sets random seeds for Python's random and NumPy."""
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
            np.random.seed(self.config.random_seed)
            logger.info(f"Set random seed to: {self.config.random_seed}")

    @abstractmethod
    def _load_scene_list(self) -> List[str]:
        """
        Abstract method to load the list of scene IDs that need processing.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _process_single_scene(self, scene_id: str) -> Dict[str, Any] | None:
        """
        Abstract method to process data for a single scene ID.
        Must be implemented by subclasses.
        Should return a dictionary of metadata for the scene, or None if processing fails.
        """
        pass

    def _save_results(self, results: Dict[str, Any]):
        """Saves the aggregated results dictionary to a JSON file."""
        output_path = os.path.join(self.config.save_dir, self.config.output_filename)
        os.makedirs(self.config.save_dir, exist_ok=True)

        if os.path.exists(output_path) and not self.config.overwrite:
            logger.error(f"Output file exists and overwrite is False: {output_path}. Aborting save.")
            return # Or raise an error if preferred

        logger.info(f"Saving aggregated metadata for {len(results)} scenes to {output_path}")
        try:
            with open(output_path, "w") as f:
                # Use separators for compact storage, indent=None for smallest file size
                # json.dump(results, f, separators=(',', ':'))
                # Or use indent=4 for human-readable output:
                json.dump(results, f, indent=4)
            logger.info(f"Successfully saved results to {output_path}")
        except Exception as e:
            logger.exception(f"Failed to save results to {output_path}: {e}") # Use logger.exception to include traceback

    def process_all_scenes(self):
        """
        Loads the scene list and processes all scenes using a multiprocessing Pool.
        Aggregates results and saves them.
        """
        scene_ids = self._load_scene_list()
        if not scene_ids:
            logger.warning("No scene IDs loaded. Exiting processing.")
            return

        aggregated_results = {}
        num_scenes = len(scene_ids)
        
        effective_workers = min(self.config.num_workers, num_scenes) # Don't use more workers than scenes
        if effective_workers <= 0:
             logger.warning("Number of workers is zero or negative. Processing sequentially.")
             effective_workers = 1
        
        logger.info(f"Starting processing for {num_scenes} scenes using {effective_workers} workers.")

        if effective_workers == 1:
             # Process sequentially for easier debugging or if only 1 worker requested
             logger.info("Processing scenes sequentially (num_workers=1)...")
             for scene_id in tqdm.tqdm(scene_ids, desc="Processing scenes"):
                 scene_id_out, result = self._process_single_scene_wrapper(scene_id)
                 if result is not None:
                     aggregated_results[scene_id_out] = result
        else:
             # Process in parallel
             logger.info(f"Processing scenes in parallel with {effective_workers} workers...")
             with Pool(processes=effective_workers) as pool:
                 # imap_unordered generally yields results as they complete
                 results_iterator = pool.imap_unordered(self._process_single_scene_wrapper, scene_ids)
                 
                 # Wrap with tqdm for progress bar
                 for scene_id_out, result in tqdm.tqdm(results_iterator, total=num_scenes, desc="Processing scenes"):
                     if result is not None:
                         aggregated_results[scene_id_out] = result
                     # Error logging happens within _process_single_scene_wrapper

        processed_count = len(aggregated_results)
        logger.info(f"Finished processing. Successfully processed {processed_count} out of {num_scenes} scenes.")
        if processed_count > 0:
             self._save_results(aggregated_results)
        else:
             logger.warning("No scenes were successfully processed. Output file will not be saved.")

    def _process_single_scene_wrapper(self, scene_id: str):
         """
         Internal wrapper to call the user-implemented _process_single_scene method.
         Handles exceptions within the worker process and returns scene_id along with the result.
         """
         try:
             # Note: Logging configuration needs to be handled correctly for multiprocessing.
             # Basic logging might work, but complex handlers might need explicit setup in workers.
             result = self._process_single_scene(scene_id)
             # Return tuple (scene_id, result) for tracking in the main process
             return scene_id, result
         except Exception as e:
              # Log the error from the worker process. Use logger.exception for full traceback.
              logger.exception(f"Error processing scene {scene_id} in worker: {e}")
              return scene_id, None # Indicate failure for this scene_id 