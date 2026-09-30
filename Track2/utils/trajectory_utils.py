import numpy as np

from . import arkitscenes_utils, scannetpp_utils, scannetv2_utils


FRAME_CATEGORY_FPS_LOOKUP_TABLE = {
    "scannet": 24,
    "scannetpp": 30,
    "arkitscenes": 10
}


def read_trajectory(dataset_name, scene_name):
    """Reads the trajectory file for a given dataset and scene.

    Args:
        dataset_name (str): _description_
        scene_name (str): _description_

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    if dataset_name == 'scannet':
        return scannetv2_utils.read_trajectory(scene_name)
    elif dataset_name == "scannetpp":
        pass
    elif dataset_name == "arkitscenes":
        pass
    else:
        raise ValueError(f"Unknown dataset name: {dataset_name}")


def get_all_image_categories_info():
    """_description_

    Args:
        scene_name (_type_): _description_

    Returns:
        _type_: _description_
    """
    scannet_path = "data/scannet_appr_order/scannet_frame_category_info.npy"
    scannetpp_path = "../data/meta_info/scannetpp_frame_category_info.npy"
    arkitscenes_path = "../data/meta_info/arkitscenes_frame_category_info.npy"

    dataset_frame_cate_infos = np.load(scannet_path, allow_pickle=True).item()
    # scannetpp_dataset_frame_cate_infos = np.load(scannetpp_path, allow_pickle=True).item()
    # arkitscenes_frame_cate_infos = np.load(arkitscenes_path, allow_pickle=True).item()

    # dataset_frame_cate_infos.update(scannetpp_dataset_frame_cate_infos)
    # dataset_frame_cate_infos.update(arkitscenes_frame_cate_infos)

    return dataset_frame_cate_infos
