import os
import zlib
import lz4.block
import glob
import torch
import json
import cv2

import numpy as np
import imageio as iio

from tqdm import tqdm
from pathlib import Path

SCANNETPP_RAW_DIR = os.environ.get("SCANNETPP_RAW_DIR", "")
SEMANTIC_LABEL_FILE = os.environ.get("SCANNETPP_SEMANTIC_LABEL_FILE", "")
SCANNETPP_META_INFO_PATH = os.environ.get("SCANNETPP_META_INFO_PATH", "")
SCANNETPP_META_INFO = None

SCANNETPP_INST_SEG_CATEGORY = ['table', 'door', 'ceiling lamp', 'cabinet', 'blinds', 'curtain', 'chair', 'storage cabinet', 'office chair', 'bookshelf', 'whiteboard', 'window', 'box', 'monitor', 'shelf', 'heater', 'kitchen cabinet', 'sofa', 'bed', 'trash can', 'book', 'plant', 'blanket', 'tv', 'computer tower', 'refrigerator', 'jacket', 'sink', 'bag', 'picture', 'pillow', 'towel', 'suitcase', 'backpack', 'crate', 'keyboard', 'rack', 'toilet', 'printer', 'poster', 'painting', 'microwave', 'shoes', 'socket', 'bottle', 'bucket', 'cushion', 'basket', 'shoe rack', 'telephone', 'file folder', 'laptop', 'plant pot', 'exhaust fan', 'cup', 'coat hanger', 'light switch', 'speaker', 'table lamp', 'kettle', 'smoke detector', 'container', 'power strip', 'slippers', 'paper bag', 'mouse', 'cutting board', 'toilet paper', 'paper towel', 'pot', 'clock', 'pan', 'tap', 'jar', 'soap dispenser', 'binder', 'bowl', 'tissue box', 'whiteboard eraser', 'toilet brush', 'spray bottle', 'headphones', 'stapler', 'marker']
SCANNETPP_INVALID_CATEGORY = [
    "box",
    "tissue box",
    "cabinet",
    "storage cabinet",
    "kitchen cabinet",
]

INVALID_CATES = [
    "binder", # only one video includes this category, and the instance is highly occluded.
    "poster",
    "blinds",
    "curtain",
    "window", # ambugious annotation, e.g., 7b6477cb95
    "backpack", # ambugious, e.g., acd95847c5
    "bag", # ambugious, 3f15a9266d
    "book", # too many instances in a single scene, e.g., 3f15a9266d
    "bottle", # ambugious and too many, e.g., 3db0a1c8f3
    "box", # sometimes very difficult for human, e.g., 5f99900f09
    # "ceiling lamp", # too hard, e.g., 578511c8a9
    "container", # somtimes ambiguous, e.g., 3864514494. Maybe can be checked by anjali.
    "jacket", # somtimes overlaped, e.g., 3db0a1c8f3
    "jar", # difficult, 09c1414f1b
    "light switch", # too small
    "marker", # marker pen, too small and ambugious
    "painting", # only in one scene, and wrong numbers. 3f15a9266d
    "paper towel", # wrong numbers, in f3685d06a9
    "poster", # poster is masked by pink
    "plant pot", # plant can be a good one, plant pot should be the same
    "pot", # only one instance in all scenes
    # "power strip", # can give it a try, but really too small
    "shelf", # ambugious, 25f3b7a318
    "sink", # ambugious, 09c1414f1b
    "smoke detector", # too small, intuitively
    "soap dispenser", # too small,
    "socket", # too small, 3864514494 
    "speaker", # too small, fb5a96b1a2
    "spray bottle", # too small,
    "tap", # too small,
    "tissue box",
    "toilet brush",
    "toilet paper",
    "towel",
    "whiteboard eraser",
    "cabinet",
    "kitchen cabinet",
    "storage cabinet",
]

CATE_MAPPER = {
    "cabinet": [
        "cabinet",
        "kitchen cabinet",
        "storage cabinet",
    ],
    "chair": [
        "chair",
        "office chair",
    ],
    "ceiling light": [
        "ceiling lamp",
    ],
    "computer mouse": [
        "mouse",
    ],
}

CATE_MAPPER_INVERSE = {}
for key, values in CATE_MAPPER.items():
    for value in values:
        CATE_MAPPER_INVERSE[value] = key



def extract_depth(scene_name):
    """extract frame wise depth

    Args:
        scene_name (_type_): _description_
    """
    scene_path = Path(os.path.join(SCANNETPP_RAW_DIR, scene_name))
    scene_iphone_depth_dir = scene_path / 'iphone' / 'depth'
    scene_iphone_depth_path = scene_path / 'iphone' / 'depth.bin'
    
    # global compression with zlib
    height, width = 192, 256
    sample_rate = 1
    scene_iphone_depth_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(scene_iphone_depth_path, 'rb') as infile:
            data = infile.read()
            data = zlib.decompress(data, wbits=-zlib.MAX_WBITS)
            depth = np.frombuffer(data, dtype=np.float32).reshape(-1, height, width)

        for frame_id in tqdm(range(0, depth.shape[0], sample_rate), desc='decode_depth'):
            iio.imwrite(f"{scene_iphone_depth_dir}/frame_{frame_id:06}.png", (depth * 1000).astype(np.uint16))
    # per frame compression with lz4/zlib
    except:
        frame_id = 0
        with open(scene_iphone_depth_path, 'rb') as infile:
            while True:
                size = infile.read(4)   # 32-bit integer
                if len(size) == 0:
                    break
                size = int.from_bytes(size, byteorder='little')
                if frame_id % sample_rate != 0:
                    infile.seek(size, 1)
                    frame_id += 1
                    continue

                # read the whole file
                data = infile.read(size)
                try:
                    # try using lz4
                    data = lz4.block.decompress(data, uncompressed_size=height * width * 2)  # UInt16 = 2bytes
                    depth = np.frombuffer(data, dtype=np.uint16).reshape(height, width)
                except:
                    # try using zlib
                    data = zlib.decompress(data, wbits=-zlib.MAX_WBITS)
                    depth = np.frombuffer(data, dtype=np.float32).reshape(height, width)
                    depth = (depth * 1000).astype(np.uint16)

                # 6 digit frame id = 277 minute video at 60 fps
                iio.imwrite(f"{scene_iphone_depth_dir}/frame_{frame_id:06}.png", depth)
                frame_id += 1


def get_image_categorys_by_projecting_to_image(scene_name):
    # load depth intrinsic
    pose_path = os.path.join(SCANNETPP_RAW_DIR, scene_name, 'iphone', 'pose_intrinsic_imu.json')
    
    pose_data = json.load(open(pose_path, 'r'))
    
    depth_paths = sorted(
        glob.glob(os.path.join(SCANNETPP_RAW_DIR, scene_name, 'iphone', 'depth/*.png')),
        key=lambda a: int(os.path.basename(a).split('.')[0].split('_')[-1])
    )
    
    # load point cloud and semantics
    pc_path = f"{SCANNETPP_RAW_DIR}/../pth_data/{scene_name}.pth"
    pc_data = torch.load(pc_path)
    xyz = pc_data['sampled_coords']
    sampled_labels = pc_data['sampled_labels']
    sampled_instance_labels = pc_data['sampled_instance_labels']
    
    semantic_names = [line.strip() for line in open(SEMANTIC_LABEL_FILE, 'r')]
    
    # loop over frames
    # the origin fps is 60, while our transformed video is 30 fps.
    original_fps = 60
    transformed_fps = 30
    skip_rate = original_fps // transformed_fps
    frame_category_dict_list = []
    for i, depth_path in tqdm(enumerate(depth_paths), total=len(depth_paths), desc='project_to_image'):
        if i % skip_rate != 0:
            continue
        
        frame_name = os.path.basename(depth_path).split('.')[0]
        
        frame_category_dict = project_single_frame(
            scene_name, xyz, pose_data[frame_name]['aligned_pose'], pose_data[frame_name]['intrinsic'], 
            depth_path, sampled_labels, sampled_instance_labels, semantic_names
        )
        frame_category_dict_list.append(frame_category_dict)
    
    assert len(frame_category_dict_list) == (len(depth_paths) + 1) // skip_rate
    return frame_category_dict_list


def check_frame_category_length_correct(scene_name, frame_category_dict_list):
    # the origin fps is 60, while our transformed video is 30 fps.
    original_fps = 60
    transformed_fps = 30
    skip_rate = original_fps // transformed_fps
    
    depth_paths = sorted(
        glob.glob(os.path.join(SCANNETPP_RAW_DIR, scene_name, 'iphone', 'depth/*.png')),
        key=lambda a: int(os.path.basename(a).split('.')[0].split('_')[-1])
    )
    
    is_valid = len(frame_category_dict_list) == (len(depth_paths) + 1) // skip_rate

    if not is_valid:
        print(f"Frame category length is not correct: {len(frame_category_dict_list)} vs {len(depth_paths) // skip_rate}")

    return is_valid


def project_single_frame(scene_name, points_world, pose, intrinsic, depth_path, label, 
                         inst_label, semantic_names, depth_image_size=(192, 256), 
                         image_size=(1440, 1920)):
    intrinsic = np.array(intrinsic)
    if image_size != None:
        scale = image_size[0] / depth_image_size[0]
        intrinsic[:1, :] = intrinsic[:1, :] / scale
        intrinsic[1:2, :] = intrinsic[1:2, :] / scale
        # depth_image_size = image_size
    
    fx = intrinsic[0, 0]
    fy = intrinsic[1, 1]
    cx = intrinsic[0, 2]
    cy = intrinsic[1, 2]
    bx = 0  # intrinsic[0, 3]
    by = 0  # intrinsic[1, 3]
    
    # == processing depth ===
    depth_img = cv2.imread(depth_path, -1)  # read 16bit grayscale image
    depth_shift = 1000.0
    depth = depth_img / depth_shift
    depth_mask = (depth_img != 0)

    # == processing pose ===
    points = np.hstack((points_world[..., :3], np.ones((points_world.shape[0], 1))))
    points = np.dot(points, np.linalg.inv(np.transpose(pose)))
    
    # == camera to image coordination ===
    u = (points[..., 0] - bx) * fx / points[..., 2] + cx
    v = (points[..., 1] - by) * fy / points[..., 2] + cy
    d = points[..., 2]
    u = (u + 0.5).astype(np.int32)
    v = (v + 0.5).astype(np.int32)
    
    # filter out invalid points
    point_valid_mask = (d >= 0) & (u < depth_image_size[1]) & (v < depth_image_size[0]) & (u >= 0) & (v >= 0)
    point_valid_idx = np.where(point_valid_mask)[0]
    point2image_coords = v * depth_image_size[1] + u
    valid_point2image_coords = point2image_coords[point_valid_idx]
    
    depth = depth.reshape(-1)
    depth_mask = depth_mask.reshape(-1)
    
    image_depth = depth[valid_point2image_coords.astype(np.int64)]
    depth_mask = depth_mask[valid_point2image_coords.astype(np.int64)]
    point2image_depth = d[point_valid_idx]
    depth_valid_mask = depth_mask & (np.abs(image_depth - point2image_depth) <= 0.2 * image_depth)
    
    point_valid_idx = point_valid_idx[depth_valid_mask]
    
    valid_label = label[point_valid_idx]
    valid_inst_label = inst_label[point_valid_idx]
    
    unique_values, counts = np.unique(valid_label, return_counts=True)
    
    category_dict = {}
    for value, count in zip(unique_values, counts):
        value = int(value)
        category_name = semantic_names[value]
        
        is_valid, category_name = category_filtering_and_remapping(scene_name, category_name)
        if is_valid:
            mask = valid_label == value
            inst_values, inst_counts = np.unique(valid_inst_label[mask], return_counts=True)
            
            category_dict[category_name] = {}
            category_dict[category_name]['num_pixels'] = count
            
            category_dict[category_name]['inst_ids'] = inst_values
            category_dict[category_name]['inst_num_pixels'] = inst_counts
    
    return category_dict


def category_filtering_and_remapping(scene_name, category_name):
    if category_name not in SCANNETPP_INST_SEG_CATEGORY or category_name in INVALID_CATES:
        return False, category_name

    tgt_cate = CATE_MAPPER_INVERSE.get(category_name, category_name)
    if magic_category_checker(scene_name, tgt_cate):
        return True, tgt_cate
    else:
        return False, tgt_cate
        

def magic_category_checker(scene_name, category_name):
    if scene_name == "cc5237fd77" and category_name == "table":
        return False
    if scene_name == "3e8bba0176" and category_name == "printer":
        return False
    if scene_name == "21d970d8de" and category_name in ["heater", "table"]:
        return False
    if scene_name == "c4c04e6d6c" and category_name in ["ceiling light", "exhaust fan", "table"]:
        return False
    if scene_name == "5ee7c22ba0" and category_name == "whiteboard":
        return False
    if scene_name == "a980334473" and category_name in ["printer", "exhaust fan"]:
        return False
    if scene_name == "f2dc06b1d2" and category_name == "exhaust fan":
        return False
    if scene_name == "bcd2436daf" and category_name in ["blanket", "suitcase"]:
        return False
    if scene_name == "0d2ee665be" and category_name in ["pillow", "blanket", "kettle"]:
        return False
    if scene_name == "09c1414f1b" and category_name == "door":
        return False
    return True


def read_trajectory(scene_name):
    trajectory_path = os.path.join(SCANNETPP_RAW_DIR, f"{scene_name}", 'all_pose_normalized.txt')
    fps = 30
    
    with open(trajectory_path, 'r') as f:
        lines = f.readlines()
    trajectory_list = []
    total_frames = len(lines)
    
    for line in lines:
        pose = [float(x) for x in line.strip().split()]
        trajectory_list.append(pose)
    
    return trajectory_list, fps, total_frames


def get_valid_category_list_by_scene_name(scene_name):
    global SCANNETPP_META_INFO
    if SCANNETPP_META_INFO is None:
        SCANNETPP_META_INFO = json.load(open(SCANNETPP_META_INFO_PATH, 'r'))
    
    return list(SCANNETPP_META_INFO[scene_name]['object_counts'].keys())

def get_valid_category_list_scannetpp():
    global SCANNETPP_META_INFO
    if SCANNETPP_META_INFO is None:
        SCANNETPP_META_INFO = json.load(open(SCANNETPP_META_INFO_PATH, 'r'))

    valid_categories = []
    for scene_name in SCANNETPP_META_INFO.keys():
        valid_categories += get_valid_category_list_by_scene_name(scene_name)
    
    return list(set(valid_categories))


if __name__ == '__main__':
    split_path = os.environ.get("SCANNETPP_SPLIT_PATH")
    if not split_path:
        raise RuntimeError("Set SCANNETPP_SPLIT_PATH before running this utility.")

    with open(split_path, 'r') as f:
        scene_names = f.readlines()

    for scene_name in tqdm(scene_names, total=len(scene_names), desc='extract_depth'):
        scene_name = scene_name.strip()
        extract_depth(scene_name)


