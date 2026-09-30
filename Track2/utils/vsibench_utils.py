MCA_QUESTION_TYPES = [
    # vsibench
    "object_rel_direction_v1",
    "object_rel_direction_v2",
    "object_rel_direction_v3",
    "object_rel_distance_v1",
    "object_rel_distance_v2",
    "object_rel_distance_v3",
    "route_planning",
    "obj_appearance_order",
    # vstibench
    "camera_obj_rel_dir",
    "obj_obj_relative_pos_lr",
    "obj_obj_relative_pos_ud",
    "obj_obj_relative_pos_nf",
    "camera_obj_rel_dist_v1",
    "camera_obj_rel_dist_v2",
    "camera_obj_rel_dist_v3",
    "camera_movement_direction",
]
NA_QUESTION_TYPES = [
    # vsibench
    "object_abs_distance",
    "object_counting",
    "object_size_estimation",
    "room_size_estimation",
    # vstibench
    "camera_obj_abs_dist",
    "camera_displacement",
    "camera_obj_dist_change",
]

LMMS_EVAL_SPECIFIC_KWARGS = {
    "pre_prompt": "These are frames of a video.",
    "na_post_prompt": "Please answer the question using a single word or phrase.",
    "mca_post_prompt": "Answer with the option's letter from the given choices directly.",
}

def vsibench_doc_to_text(doc, lmms_eval_specific_kwargs=LMMS_EVAL_SPECIFIC_KWARGS):
    question = doc["question"]
        
    pre_prompt = lmms_eval_specific_kwargs.get("pre_prompt", "") or "These are frames of a video."
    
    if doc['question_type'] in NA_QUESTION_TYPES:
        post_prompt = lmms_eval_specific_kwargs.get("na_post_prompt", "") or "Please answer the question using a single word or phrase."
        return pre_prompt + "\n" + question + "\n" + post_prompt
    elif doc['question_type'] in MCA_QUESTION_TYPES:
        options = "Options:\n" + "\n".join(doc["options"])
        post_prompt = lmms_eval_specific_kwargs.get("mca_post_prompt", "") or "Answer with the option's letter from the given choices directly."
        return "\n".join([pre_prompt, question, options, post_prompt])
    else:
        raise ValueError(f"Unknown question type: {doc['question_type']}")