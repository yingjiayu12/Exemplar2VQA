import numpy as np
import json
import math
import random

FPS_LOOKUP = {
    "scannet": 24,
    "arkitscenes": 30,
    "scannetpp": 30
}


def load_scene_list(split_path):
    with open(split_path, "r") as f:
        scene_list = [line.strip() for line in f if line.strip()]
    return scene_list


def load_meta_info(meta_info_path):
    with open(meta_info_path, "r") as f:
        annos = json.load(f)
    return annos


def generate_multiple_choice(ground_truth, margin=0.20, lower_bound=0.25, upper_bound=1.75, 
                             decimals=1, answer_counts=None, option_letters=None):
    EPS = math.ceil(ground_truth * margin * (10 ** decimals)) / (10 ** decimals) # scaling ceiling value to precision specified by decimals

    def sample_choices(ground_truth, lower_bound=lower_bound, upper_bound=upper_bound):
        lower_bound = ground_truth * lower_bound
        upper_bound = ground_truth * upper_bound
        choices = [random.uniform(lower_bound, upper_bound) for _ in range(3)]

        return [int(round(choice)) if decimals == 0 else round(choice, decimals) for choice in choices]
    
    def too_close(choices, ground_truth):
        return any(abs(choice - other) < EPS for i, choice in enumerate(choices) for other in choices[i+1:] + [ground_truth])

    choices = sample_choices(ground_truth)

    # Re-sample if any two choices are within epsilon of each other
    # If two choices are too close to each other it could make model's choice easier / harder
    max_attempts = 30  # to prevent an infinite loop
    attempts = 0
    while too_close(choices, ground_truth) and attempts <= max_attempts:
        # choices = sample_choices(ground_truth)

        # Re-sample only the choices that are too close to the others
        for i in range(len(choices)):
            if any(abs(choices[i] - other) < EPS for other in choices[:i] + choices[i+1:] + [ground_truth]):
                # Resample this choice
                new_choice = random.uniform(ground_truth * lower_bound, ground_truth * upper_bound)
                choices[i] = int(round(new_choice)) if decimals == 0 else round(new_choice, decimals)

        attempts += 1

    if too_close(choices, ground_truth):
        return [], "E", answer_counts  # E for Error
    
    # Add the GT to the three false answers
    choices.append(ground_truth)

    # Shuffle the choices
    # random.shuffle(choices)
    # correct_index = choices.index(ground_truth)
    
    # options = ['A', 'B', 'C', 'D']
    # correct_option = options[correct_index]
    options, mc_answer, answer_counts = from_options_to_mc_answer(
        choices, ground_truth, answer_counts, option_letters
    )
    
    return options, mc_answer, answer_counts


def sample_points_in_oriented_bbox_uniform(bbox, distance=0.05):
    import open3d as o3d

    # Calculate number of points along each dimension
    nx = int(np.ceil(bbox.extent[0] / distance))
    ny = int(np.ceil(bbox.extent[1] / distance))
    nz = int(np.ceil(bbox.extent[2] / distance))

    # Generate uniform grid
    x = np.linspace(-bbox.extent[0]/2, bbox.extent[0]/2, nx)
    y = np.linspace(-bbox.extent[1]/2, bbox.extent[1]/2, ny)
    z = np.linspace(-bbox.extent[2]/2, bbox.extent[2]/2, nz)
    
    # Create meshgrid
    xx, yy, zz = np.meshgrid(x, y, z)
    
    # Reshape to (N, 3) array
    points = np.vstack([xx.ravel(), yy.ravel(), zz.ravel()]).T

    # Create a mask for points to keep (outside the inner box)
    mask = np.any(np.abs(points) > bbox.extent / 4, axis=1)
    points = points[mask]

    # Rotate points
    R = bbox.R
    points = np.dot(points, R.T)

    # Translate points to bbox center
    points += bbox.center

    # Create Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    # Crop points to ensure they're all within the bounding box
    pcd = pcd.crop(bbox)
    
    if len(pcd.points) == 0:
        return sample_points_in_oriented_bbox_uniform(bbox, distance=distance*0.5)

    return np.asarray(pcd.points)


def cal_3d_bbox_distance_between_categories(cate1_bbox_info, cate2_bbox_info):
    import open3d as o3d
    from scipy.spatial.distance import cdist

    # build bounding boxes list
    cate1_bbox_list = []
    for ins in cate1_bbox_info:
        cate1_bbox = o3d.geometry.OrientedBoundingBox(
            center=np.array(ins["centroid"]).astype(np.float64).reshape(3, 1),
            R=np.array(ins["normalizedAxes"]).astype(np.float64).reshape(3, 3).T,
            extent=np.array(ins["axesLengths"]).astype(np.float64).reshape(3, 1)
        )
        cate1_bbox_list.append(cate1_bbox)

    cate2_bbox_list = []
    for ins in cate2_bbox_info:
        cate2_bbox = o3d.geometry.OrientedBoundingBox(
            center=np.array(ins["centroid"]).astype(np.float64).reshape(3, 1),
            R=np.array(ins["normalizedAxes"]).astype(np.float64).reshape(3, 3).T,
            extent=np.array(ins["axesLengths"]).astype(np.float64).reshape(3, 1)
        )
        cate2_bbox_list.append(cate2_bbox)

    # calculate distance
    ins_distance_matrix = np.zeros((len(cate1_bbox_list), len(cate2_bbox_list)))
    
    for i, cate1_bbox in enumerate(cate1_bbox_list):
        for j, cate2_bbox in enumerate(cate2_bbox_list):
            point_set1 = sample_points_in_oriented_bbox_uniform(cate1_bbox)
            point_set2 = sample_points_in_oriented_bbox_uniform(cate2_bbox)

            distances = np.min(cdist(point_set1, point_set2, 'euclidean'))
            ins_distance_matrix[i, j] = distances

    min_distance = np.min(ins_distance_matrix)

    return min_distance


def extract_cared_categories_from_qa(qa_pair):
    # determine category(s) at hand
    if qa_pair['question_type'] in ['room_size_estimation', 'route_planning']:
        categories = []
    elif qa_pair['question_type'] == 'object_abs_distance':
        categories = [qa_pair['category, first object'], qa_pair['category, second object']]
    elif qa_pair['question_type'] in ['object_rel_direction_v1', 'object_rel_direction_v2', 'object_rel_direction_v3']:
        categories = [qa_pair['category, positioning object'], qa_pair['category, orienting object'], qa_pair['category, querying object']]
    elif qa_pair['question_type'] == 'object_rel_distance':
        # four options plus the main object
        categories = [item.split(". ")[1] for item in qa_pair['options']]
        categories.append(qa_pair['category'])
    elif qa_pair['question_type'] == 'obj_appearance_order':
        categories = [item.strip() for item in qa_pair['ground_truth'].split(",")]
    elif qa_pair['question_type'] in ['object_size_estimation', 'object_counting']:
        categories = [qa_pair['category']]
    else:
        raise NotImplementedError(f"Question type {qa_pair['question_type']} not implemented yet.")
    
    return categories


def from_options_to_mc_answer(options, gt, answer_counts, option_letters):
    # Find the letter with the minimum count
    min_count = min(answer_counts.values())
    min_letters = [letter for letter, count in answer_counts.items() 
                   if count == min_count and letter in option_letters[:len(options)]]
    
    if min_letters:
        # Choose one of the minimum count letters randomly
        target_letter = random.choice(min_letters)
        target_index = option_letters.index(target_letter)
        
        # Rearrange options to put the correct answer in the target position
        correct_option = options[options.index(gt)]
        options.remove(correct_option)
        random.shuffle(options)
        
        final_options = options[:target_index] + [correct_option] + options[target_index:]
        if len(final_options) < len(options) + 1:
            final_options.extend(options[:(len(options) + 1 - len(final_options))])
    else:
        # Fallback to original random behavior
        random.shuffle(options)
        target_index = options.index(gt)
        final_options = options
        target_letter = option_letters[target_index]
    
    # Update answer counts
    answer_counts[target_letter] += 1
    
    # Format options with letters
    # new_options = [f"{option_letters[i]}. {opt}" for i, opt in enumerate(final_options)]
    
    return final_options, target_letter, answer_counts

def calculate_room_area(xyz):
    import alphashape

    points = xyz[:, :2]
    # random sample 10k points to reduce computational cost
    sampled_idx = np.random.choice(points.shape[0], 10000)
    sampled_points = points[sampled_idx]
    alpha_shape = alphashape.alphashape(sampled_points[:, :2], alpha=5)
    # NOTE: argument `alpha` plays a quite important role in alphashape algorithm!
    return alpha_shape.area

def calculate_room_center(xyz):
    """
    Calculate the center of a room using the minimal oriented bounding box.
    
    Args:
        xyz: Numpy array of 3D points representing the room
    
    Returns:
        The center coordinates of the room's minimal oriented bounding box
    """
    import open3d as o3d

    # Convert points to Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
    
    # Get minimal oriented bounding box and its center
    bbox = pcd.get_minimal_oriented_bounding_box()
    return bbox.center.tolist()
