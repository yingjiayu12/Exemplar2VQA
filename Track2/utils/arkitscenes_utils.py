import os
import glob
import json

import numpy as np

ARKITSCENES_3DOD_DIR = os.environ.get("ARKITSCENES_3DOD_DIR", "")


INVALID_CATES = [
    "sink",
    "shelf",
    "oven",
    "cabinet"
]
CATE_MAPPER = {
    "tv": [
        "tv_monitor",
    ],
}

CATE_MAPPER_INVERSE = {}
for key, values in CATE_MAPPER.items():
    for value in values:
        CATE_MAPPER_INVERSE[value] = key



def get_image_categorys_by_projecting_to_image(scene_name):
    """_description_

    Args:
        scene_name (_type_): _description_

    Returns:
        _type_: _description_
    """
    scene_dir = os.path.join(ARKITSCENES_3DOD_DIR, scene_name, f'{scene_name}_online_prepared_data', f'{scene_name}_label')
    all_frames = sorted(
        glob.glob(os.path.join(scene_dir, '*.npy')),
        key=lambda a: int(os.path.basename(a).split('.')[0].split('_')[-2])
    )
    
    # this will be 10 fps....
    frame_category_dict_list = []
    for frame in all_frames:
        frame_data = np.load(frame, allow_pickle=True).item()
        category_dict = {}
        
        valid_mask = frame_data['bboxes_mask']
        
        for idx, is_valid in enumerate(valid_mask):
            if not is_valid:
                continue
            
            category = frame_data['types'][idx]
            is_valid_cate, category = category_filtering_and_remapping(category)
            
            if not is_valid_cate:
                continue
            
            if category not in category_dict:
                category_dict[category] = {}
            
                category_dict[category]['num_pixels'] = frame_data['pts_cnt'][idx]
                category_dict[category]['inst_ids'] = [frame_data['uids'][idx]]
                category_dict[category]['inst_num_pixels'] = [frame_data['pts_cnt'][idx]]
            else:
                category_dict[category]['num_pixels'] += frame_data['pts_cnt'][idx]
                if frame_data['uids'][idx] not in category_dict[category]['inst_ids']:
                    category_dict[category]['inst_ids'].append(frame_data['uids'][idx])
                    category_dict[category]['inst_num_pixels'].append(frame_data['pts_cnt'][idx])
                else:
                    inst_idx = category_dict[category]['inst_ids'].index(frame_data['uids'][idx])
                    category_dict[category]['inst_num_pixels'][inst_idx] += frame_data['pts_cnt'][idx]

        frame_category_dict_list.append(category_dict)
    
    return frame_category_dict_list


def category_filtering_and_remapping(category_name):
    if category_name in INVALID_CATES:
        return False, category_name

    tgt_cate = CATE_MAPPER_INVERSE.get(category_name, category_name)
    return True, tgt_cate


def get_valid_category_list_by_scene_name(scene_name):
    global ARKITSCENES_META_INFO
    
    return list(ARKITSCENES_META_INFO[scene_name]['object_counts'].keys())

def get_valid_category_list_arkitscenes():
    global ARKITSCENES_META_INFO

    valid_categories = []
    for scene_name in ARKITSCENES_META_INFO.keys():
        valid_categories += get_valid_category_list_by_scene_name(scene_name)
    
    return list(set(valid_categories))
