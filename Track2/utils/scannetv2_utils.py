import open3d as o3d
import os
import torch
import numpy as np
import json
import glob
import cv2

from scipy.spatial.distance import cdist

from .scannet200_utils import SCANNET200_VALID_CATEGORY_NAME, SCANNET200_CLASS_NAMES, \
    SCANNET200_VALID_CATEGORY_IDX, SCANNET200_CLASS_REMAPPER_LIST, SCANNET200_CLASS_REMAPPER


SCANNETV2_OBJECT_CATEGORY = ['wall', 'floor', 'cabinet', 'bed', 'chair', 'sofa', 
                             'table', 'door', 'window', 'bookshelf', 'picture', 'counter',
                             'desk', 'curtain', 'refrigerator', 'showercurtain', 'toilet', 
                             'sink', 'bathtub', 'otherfurniture']


SCANNETV2_VALID_CATEGORY_NAME = ['bed', 'chair', 'sofa', 'table',
                                 'window', 'bookshelf', 'counter',
                                 'desk', 'refrigerator']


SCANNETV2_VALID_CATEGORY_IDX = [SCANNETV2_OBJECT_CATEGORY.index(name) for name in SCANNETV2_VALID_CATEGORY_NAME]


SCANNET_CLASS_REMAPPER = {
    'table': ['desk', 'table'],
}

SCANNET_CLASS_REMAPPER_LIST = ['desk', 'table']


def cal_point_set_distance_between_categories(category1, category2, scene_name, data_dir='../data/'):
    """
    Args:
        category1 (str): category name
        category2 (str): category name
    Returns:
        distance (float): the closet distance between two categories
    """
    # TODO: this assert was failing.....!! even when I used coreset
    assert category1 in SCANNETV2_VALID_CATEGORY_NAME or category1 in SCANNET200_VALID_CATEGORY_NAME
    assert category2 in SCANNETV2_VALID_CATEGORY_NAME or category2 in SCANNET200_VALID_CATEGORY_NAME

    pc_dir_scannet = os.path.join(data_dir, 'scannet', 'scans')
    pc_dir_scannet200 = os.path.join(data_dir, 'scannet200', 'scans')
    
    # load point set of category1
    if category1 in SCANNETV2_VALID_CATEGORY_NAME:
        category1_idx = SCANNETV2_OBJECT_CATEGORY.index(category1)
        pc_path1 = os.path.join(pc_dir_scannet, f'{scene_name}.pth')
    else:
        category1_idx = SCANNET200_CLASS_NAMES.index(category1)
        pc_path1 = os.path.join(pc_dir_scannet200, f'{scene_name}.pth')

    xyz, rgb, label, inst_label, *others = torch.load(pc_path1)

    cate1_inst_list = get_inst_pc_list_by_category(category1_idx, xyz, label, inst_label)
    
    # load point set of category2
    if category2 in SCANNETV2_VALID_CATEGORY_NAME:
        category2_idx = SCANNETV2_OBJECT_CATEGORY.index(category2)
        pc_path2 = os.path.join(pc_dir_scannet, f'{scene_name}.pth')
    else:
        category2_idx = SCANNET200_CLASS_NAMES.index(category2)
        pc_path2 = os.path.join(pc_dir_scannet200, f'{scene_name}.pth')

    xyz, rgb, label, inst_label, *others = torch.load(pc_path2)

    cate2_inst_list = get_inst_pc_list_by_category(category2_idx, xyz, label, inst_label)

    # calculate the closet distance between two categories
    if not cate1_inst_list or not cate2_inst_list:
        return -1

    distance = closest_distance_between_pc_lists(cate1_inst_list, cate2_inst_list)

    return distance


def get_inst_pc_list_by_category(category_idx, xyz, label, inst_label):
    """
    Args:
        category_idx (int): category index
        xyz (np.ndarray): point cloud
        label (np.ndarray): semantic label
        inst_label (np.ndarray): instance label
    Returns:
        category_pc (np.ndarray): point cloud of the category
    """

    semantic_mask = (label == category_idx)

    if semantic_mask.sum() == 0:
        return None

    cate_inst_label = inst_label[semantic_mask]
    cate_xyz = xyz[semantic_mask]

    unique_inst_label = np.unique(cate_inst_label)

    instance_pc_list = []
    for inst_id in unique_inst_label:
        inst_mask = (cate_inst_label == inst_id)
        inst_xyz = cate_xyz[inst_mask]
        instance_pc_list.append(inst_xyz)

    return instance_pc_list


def closest_distance_between_pc_lists(list1, list2):
    # Concatenate all points from list1 and list2
    points1 = np.concatenate(list1, axis=0)
    points2 = np.concatenate(list2, axis=0)

    # Calculate pairwise distances between all points
    distances = cdist(points1, points2, 'euclidean')

    # Find the minimum distance
    min_distance = np.min(distances)

    return min_distance


def get_objects_number_and_bbox(xyz, label, inst_label, valid_category_idx, object_category):
    object_num = {}
    object_bbox = {}
    for category_idx in valid_category_idx:
        semantic_mask = (label == category_idx)
        if semantic_mask.sum() == 0:
            continue

        category_name = object_category[category_idx]
        cur_inst_label = inst_label[semantic_mask]
        cur_xyz = xyz[semantic_mask]
        unique_inst_label = np.unique(cur_inst_label)

        object_num[category_name] = len(unique_inst_label)

        for inst_id in unique_inst_label:
            inst_mask = (cur_inst_label == inst_id)
            inst_xyz = cur_xyz[inst_mask]

            # inst_center = get_point_set_center(inst_xyz)
            # inst_center = np.mean(inst_xyz, axis=0).tolist()

            bbox = get_object_boxes(inst_xyz)

            # old format
            # obj_center = bbox.get_center().tolist()
            # obj_extent = bbox.extent.tolist()
            # obj_bbox = obj_center + obj_extent
            # object_bbox[category_name] = object_bbox.get(category_name, []) + [obj_bbox]

            # new format
            object_bbox[category_name] = object_bbox.get(category_name, []) + [{
                'centroid': bbox.get_center().tolist(),
                'axesLengths': bbox.extent.tolist(),
                'normalizedAxes': bbox.R.T.flatten().tolist(),
                'min': bbox.get_min_bound().tolist(),
                'max': bbox.get_max_bound().tolist(),
                'instance_id': int(inst_id)
            }]

    return object_num, object_bbox


def get_object_boxes(points):
    # Create a point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points.astype(np.float64))

    # Create the oriented bounding box
    bbox = pcd.get_minimal_oriented_bounding_box()
    
    return bbox


def read_trajectory(scene_name):
    trajectory_path = os.path.join(SCANNET_RAW_DIR, f"{scene_name}", 'all_pose_normalized.txt')
    fps = 24
    
    with open(trajectory_path, 'r') as f:
        lines = f.readlines()
    trajectory_list = []
    total_frames = len(lines)
    
    for line in lines:
        pose = [float(x) for x in line.strip().split()]
        trajectory_list.append(pose)
    
    return trajectory_list, fps, total_frames


def get_image_categories_by_projecting_to_image(scene_name):
    """_summary_

    Args:
        scene_name (_type_): _description_

    Returns:
        frame_category_dict_list: category dict for each frame in the video
    """
    depth_intrinsic_path = os.path.join(SCANNET_RAW_DIR, f"{scene_name}", 'intrinsic/intrinsic_depth.txt')

    pose_paths = sorted(
        glob.glob(os.path.join(SCANNET_RAW_DIR, scene_name, 'pose/*.txt')),
        key=lambda a: int(os.path.basename(a).split('.')[0])
    )
    
    depth_paths = sorted(
        glob.glob(os.path.join(SCANNET_RAW_DIR, scene_name, 'depth/*.png')),
        key=lambda a: int(os.path.basename(a).split('.')[0])
    )
    
    depth_intrinsic = np.loadtxt(depth_intrinsic_path)
    
    pc_means = json.load(open(f'{SCANNET_RAW_DIR}/../../pc_means_new.json', 'r'))
    
    # load point cloud for scannet
    pc_path = os.path.join(SCANNET_RAW_DIR, '../../scans', f"{scene_name}.pth")
    pc_path_200 = os.path.join(SCANNET_RAW_DIR, '../../../scannet200/scans', f"{scene_name}.pth")
    
    xyz, rgb, label_20, inst_label_20, *others = torch.load(pc_path)
    _, rgb, label_200, inst_label_200, *others = torch.load(pc_path_200)
    
    points_xyz = xyz + np.array(pc_means[scene_name]).reshape(-1, 3)
    
    frame_category_dict_list = []
    for depth_path, pose_path in zip(depth_paths, pose_paths):
        frame_category_dict = project_single_frame(
            points_xyz, label_20, inst_label_20, label_200, inst_label_200, pose_path, depth_path, depth_intrinsic
        )
        frame_category_dict_list.append(frame_category_dict)

    return frame_category_dict_list


def project_single_frame(points_world, label_20, inst_label_20, label_200, inst_label_200, 
                         pose_path, depth_path, depth_intrinsic, depth_image_size=(480, 640)):
    """_summary_

    Args:
        points_world (_type_): _description_
        label (_type_): _description_
        inst_label (_type_): _description_
        pose_path (_type_): _description_
        depth_path (_type_): _description_
        depth_intrinsic (_type_): _description_
        depth_image_size (tuple, optional): _description_. Defaults to (480, 640).

    Returns:
        category_dict: {
            category_name: {
                num_pixels: int, number of pixels of the category in current frame
                inst_ids: np.ndarray, different instance ids of the category in current frame
                inst_num_pixels: np.ndarray, number of pixels of each instance of the category in current frame
            }
        }
    """
    fx = depth_intrinsic[0, 0]
    fy = depth_intrinsic[1, 1]
    cx = depth_intrinsic[0, 2]
    cy = depth_intrinsic[1, 2]
    bx = depth_intrinsic[0, 3]
    by = depth_intrinsic[1, 3]

    # == processing depth ===
    depth_img = cv2.imread(depth_path, -1)  # read 16bit grayscale image
    depth_shift = 1000.0
    depth = depth_img / depth_shift
    depth_mask = (depth_img != 0)
    
    # == processing pose ===
    pose = np.loadtxt(pose_path)
    
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
    
    valid_label_20 = label_20[point_valid_idx]
    valid_inst_label_20 = inst_label_20[point_valid_idx]
    unique_values_20, counts = np.unique(valid_label_20, return_counts=True)
    
    # for scannet20
    category_dict = {}
    for value, count in zip(unique_values_20, counts):
        value = int(value)
        if value in SCANNETV2_VALID_CATEGORY_IDX:
            category_name = SCANNETV2_OBJECT_CATEGORY[value]
            
            mask = valid_label_20 == value
            inst_values, inst_counts = np.unique(valid_inst_label_20[mask], return_counts=True)
            
            if category_name in SCANNET_CLASS_REMAPPER_LIST:
                for src, tgt in SCANNET_CLASS_REMAPPER.items():
                    if category_name in tgt:
                        category_name = src
                        break
            
            if category_name not in category_dict:
                category_dict[category_name] = {}
                category_dict[category_name]['num_pixels'] = count
                
                category_dict[category_name]['inst_ids'] = inst_values
                category_dict[category_name]['inst_num_pixels'] = inst_counts
            else:
                category_dict[category_name]['num_pixels'] += count
                
                category_dict[category_name]['inst_ids'] = np.concatenate(
                    (category_dict[category_name]['inst_ids'], inst_values), axis=0
                )
                category_dict[category_name]['inst_num_pixels'] = np.concatenate(
                    (category_dict[category_name]['inst_num_pixels'], inst_counts), axis=0
                )
    
    # for scanent200
    valid_label_200 = label_200[point_valid_idx]
    valid_inst_label_200 = inst_label_200[point_valid_idx]
    
    unique_values_200, counts_200 = np.unique(valid_label_200, return_counts=True)
    
    for value, count in zip(unique_values_200, counts_200):
        value = int(value)
        if value in SCANNET200_VALID_CATEGORY_IDX:
            category_name = SCANNET200_CLASS_NAMES[value]
            
            mask = valid_label_200 == value
            inst_values, inst_counts = np.unique(valid_inst_label_200[mask], return_counts=True)
            
            if category_name in SCANNET200_CLASS_REMAPPER_LIST:
                for src, tgt in SCANNET200_CLASS_REMAPPER.items():
                    if category_name in tgt:
                        category_name = src
                        break
            
            if category_name not in category_dict:
                category_dict[category_name] = {}
                category_dict[category_name]['num_pixels'] = count

                category_dict[category_name]['inst_ids'] = inst_values
                category_dict[category_name]['inst_num_pixels'] = inst_counts
            else:
                category_dict[category_name]['num_pixels'] += count

                category_dict[category_name]['inst_ids'] = np.concatenate(
                    (category_dict[category_name]['inst_ids'], inst_values), axis=0
                )
                category_dict[category_name]['inst_num_pixels'] = np.concatenate(
                    (category_dict[category_name]['inst_num_pixels'], inst_counts), axis=0
                )
    
    return category_dict


def get_valid_category_list_by_scene_name(scene_name):
    global SCANNET_META_INFO
    
    return list(SCANNET_META_INFO[scene_name]['object_counts'].keys())


def get_valid_category_list_arkitscenes():
    global ARKITSCENES_META_INFO

    valid_categories = []
    for scene_name in ARKITSCENES_META_INFO.keys():
        valid_categories += get_valid_category_list_by_scene_name(scene_name)
    
    return list(set(valid_categories))
