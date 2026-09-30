OBJ_COUNT_TEMPLATE = """
How many {category}(s) are in this room?
""".strip()

OBJ_SIZE_ESTIMATE_TEMPLATE = """
What is the length of the longest dimension (length, width, or height) of the {category}, measured in centimeters?""".strip()

ROOM_SIZE_TEMPLATE = """
What is the size of this room (in square meters)? 
If multiple rooms are shown, estimate the size of the combined space.
""".strip()

OBJ_ABS_DISTANCE_TEMPLATE = """
Measuring from the closest point of each object, what is the direct distance between the {object1} and the {object2} (in meters)?
""".strip()

OBJ_REL_DISTANCE_V1_TEMPLATE = """
Measuring from the closest point of each object, which of these objects ({choice_a}, {choice_b}, {choice_c}, {choice_d}) is the closest to the {category}?
If there are multiple instances of an object category, measure to the closest.
""".strip()

OBJ_REL_DISTANCE_V2_TEMPLATE = """
Measuring from the closest point of each object, which of these objects ({choice_a}, {choice_b}, {choice_c}) is the closest to the {category}?
If there are multiple instances of an object category, measure to the closest.
""".strip()

OBJ_REL_DISTANCE_V3_TEMPLATE = """
Measuring from the closest point of each object, which of these objects ({choice_a}, {choice_b}) is the closest to the {category}?
If there are multiple instances of an object category, measure to the closest.
""".strip()

OBJ_REL_DIRECTION_V1_TEMPLATE = """
If I am standing by the {positioning_object} and facing the {orienting_object}, is the {querying_object} to my front-left, front-right, back-left, or back-right?
Assume "standing by" means I am positioned at the center of the {positioning_object}.
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
""".strip()

OBJ_REL_DIRECTION_V2_TEMPLATE = """
If I am standing by the {positioning_object} and facing the {orienting_object}, is the {querying_object} to my left, right, or back?
Assume "standing by" means I am positioned at the center of the {positioning_object}.
An object is to my back if I would have to turn at least 135 degrees in order to face it.
""".strip()

OBJ_REL_DIRECTION_V3_TEMPLATE = """
If I am standing by the {positioning_object} and facing the {orienting_object}, is the {querying_object} to the left or the right of the {orienting_object}?
Assume "standing by" means I am positioned at the center of the {positioning_object}.
""".strip()


OBJ_SPTP_DISTANCE_TEMPLATE = """
Which of the these objects ({choice_a}, {choice_b}, {choice_c}, {choice_d}) is the closest to the ego-position at the last frame in the video?
""".strip()


OBJ_APPEARANCE_ORDER_TEMPLATE = """
What will be the first-time appearance order of the following categories in the video: {choice_a}, {choice_b}, {choice_c}, {choice_d}?
""".strip()

ROUTE_PLAN_TEMPLATE = """
You are a robot beginning at the {start_object} facing the {facing_object}. You want to navigate to the {destination_object}. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn right.'): {actions}
""".strip()

# Camera-to-object absolute distance template
VSTI_CAMERA_OBJ_DIST_TEMPLATE = """
What is the approximate distance (in meters) between the camera (or the person filming) and the nearest point of the {object_name} in {frame_description}?
""".strip()


# Camera-to-object relative distance template
VSTI_CAMERA_OBJ_REL_DIST_TEMPLATE_V1 = """
Measuring from the closest point of each object, which of these objects ({choice_a}, {choice_b}, {choice_c}, {choice_d}) is the closest to the camera in {frame_description}?
""".strip()

VSTI_CAMERA_OBJ_REL_DIST_TEMPLATE_V2 = """
Measuring from the closest point of each object, which of these objects ({choice_a}, {choice_b}, {choice_c}) is the closest to the camera in {frame_description}?
""".strip()

VSTI_CAMERA_OBJ_REL_DIST_TEMPLATE_V3 = """
Measuring from the closest point of each object, which of these objects ({choice_a}, {choice_b}) is the closest to the camera in {frame_description}?
""".strip()

# Object-to-object relative position template
VSTI_OBJ_OBJ_REL_POS_NF_TEMPLATE = """
In {frame_description}, relative to the camera, is {obj_A_name} [Near/Far] compared to {obj_B_name}?
""".strip()

# Object-to-object relative position template
VSTI_OBJ_OBJ_REL_POS_LR_TEMPLATE = """
In {frame_description}, relative to {obj_B_name}, is {obj_A_name} to the [Left/Right]?
""".strip()

# Object-to-object relative position template
VSTI_OBJ_OBJ_REL_POS_UD_TEMPLATE = """
In {frame_description}, relative to {obj_B_name}, is {obj_A_name} to the [Up/Down]?
""".strip()

# Camera motion (translation) template V1 (4 choices)
VSTI_CAMERA_MOVEMENT_DIRECTION_TEMPLATE_V1 = """
During the sequence between {start_frame_description} and {end_frame_description}, what was the primary consistent direction of the camera's movement relative to its orientation at the start? The options are {choice_a}, {choice_b}, {choice_c}, and {choice_d}.
""".strip()

# Camera motion (translation) template V2 (3 choices)
VSTI_CAMERA_MOVEMENT_DIRECTION_TEMPLATE_V2 = """
During the sequence between {start_frame_description} and {end_frame_description}, what was the primary consistent direction of the camera's movement relative to its orientation at the start? The options are {choice_a}, {choice_b}, and {choice_c}.
""".strip()

# Camera motion (translation) template V3 (2 choices)
VSTI_CAMERA_MOVEMENT_DIRECTION_TEMPLATE_V3 = """
During the sequence between {start_frame_description} and {end_frame_description}, what was the primary consistent direction of the camera's movement relative to its orientation at the start? The options are {choice_a} and {choice_b}.
""".strip()

# Camera displacement template
VSTI_CAMERA_DISPLACEMENT_TEMPLATE = """
Approximately how far (in meters) did the camera move between {start_frame_description} and {end_frame_description}?
""".strip()

# new
CHECK_OBJ_COUNT_TEMPLATE = """
Are there at least {count} {category}(s) in this room?
""".strip()

# Viewpoint Rotation Reasoning Template
VIEWPOINT_ROTATION_TEMPLATE = """
If you are at the {source_viewpoint} viewpoint and turn {degrees} degrees to the {direction}, what object is immediately to your {target_direction}?
""".strip()

# Viewpoint Object-to-object relative position Template
VIEWPOINT_OBJ_REL_DIRECTION_TEMPLATE = """
If you are positioned at the {viewpoint_description}, what is located entirely to the {direction} of the {reference_object} from where you stand?
""".strip()

# Viewpoint Movement Proximity Template
# {proximity_phrase} can be filled with:
#   1. "get closer to" 
#   2. "get farther from"
VIEWPOINT_MOVEMENT_PROXIMITY_TEMPLATE = """
If you are positioned at {viewpoint}, then turn {turn_direction} and start moving forward, will you immediately {proximity_phrase} the {target_object}?
""".strip()

# Camera-to-Camera relative position template (Base/Open-ended)
# Context: Establishes the ego-centric frame at ref_image, asks for location of target_image.
CAM_TO_CAM_REL_POS_TEMPLATE = """
When you took {ref_image_name}, where was the camera for {target_image_name}, relative to you?
""".strip()

# Camera-to-Object relative direction template
# Context: Asks for the direction of an object relative to the camera's ego-centric frame in a specific image.
CAM_OBJ_REL_DIR_TEMPLATE = """
Which direction is the {obj_name} relative to me when I am taking {image_name}?
""".strip()

# Context-based Object-to-Object Cardinal Direction
# Example: "The deer's head sits west of the statue. Where is the mural positioned relative to the statue?"
OBJ_CONTEXT_REL_DIRECTION_TEMPLATE = """
The {context_obj} sits {context_dir} of the {ref_obj}. Where is the {target_obj} positioned relative to the {ref_obj}?
""".strip()

# Object Max Dimension Comparison Template
# Context: Compares two objects based on their absolute longest dimension regardless of orientation.
# Clarification: Explicitly defines "longer" as the max of L, W, or H.
OBJ_MAX_DIM_COMPARE_TEMPLATE = """
Which is longer, considering the length of the longest dimension (length, width, or height): the {obj1} or the {obj2}?
""".strip()

CAMERA_MOVEMENT_TEMPLATE = """
Based on the continuous images, in which direction is the camera rotating?
""".strip()

# Entry-based Object Relative Position Template (Fixed to Door)
# Context: Establishes the agent's frame of reference at the door, facing into the room.
ENTRY_DOOR_REL_POS_TEMPLATE = """
When entering the room through the door, where is the {target_obj} located relative to your position?
""".strip()

# Camera Frame Object Relative Direction Template
# Context: Asks for the direction of an object relative to the camera's local frame 
# at a specific moment in the movement sequence.
# {order_desc} examples: "first", "second", "last", "final"
FRAME_OBJ_REL_DIR_TEMPLATE = """
When you are taking the {order_desc} image, in which direction is the {obj_name} located relative to you?
""".strip()

# Anchored Cardinal Direction Template
# Context: Determines the compass direction of a target relative to a reference,
# by fixing the scene orientation using a wall-mounted anchor object.
# Example: "In which direction is the painting relative to the desk (with the whiteboard on the North wall)?"
ANCHORED_CARDINAL_DIR_TEMPLATE = """
In which direction is the {target_obj} relative to the {ref_obj} (with the {anchor_obj} on the {wall_direction} wall)?
""".strip()

# Conditional Object Relative Direction Template
# Context: First establishes scene orientation using a relationship between two objects,
# then asks for the direction of a target object relative to a specific reference object.
# Example: "The pink bench is east of the bed. Where is the toilet located relative to the sink?"
CONDITION_OBJ_REL_DIR_TEMPLATE = """
The {cond_obj_1} is {cond_dir} of the {cond_obj_2}. Where is the {target_obj} located relative to the {ref_obj}?
""".strip()

EXACT_OBJ_COUNT_TEMPLATE = """
How many {category}(s) are in this room?
""".strip()

CLOSEST_OBJ_TEMPLATE = """
Measuring from the closest point of each object, which of these objects ({choices_str}) is the closest to the {target_obj} in this room?
""".strip()

EGO_DIR_TEMPLATE = """
If I am standing by the {anchor_cat} and facing the closest {ref_cat}, is the closest {target_cat} to my front, back, left, right, front-left, front-right, back-left, or back-right in this room?
""".strip()

OBJ_COUNT_COMPARE_TEMPLATE = """
Are there fewer {obj1} than {obj2}? Please reply with a "yes" or "no" only.
""".strip()

DIST_COMPARE_TEMPLATE = """
Is the distance between the {obj1} and the {obj2} greater than the distance between the {obj3} and the {obj4}? Please reply with a "yes" or "no" only.
""".strip()

BBOX_SIZE_COMPARE_TEMPLATE = """
Is the size of the bounding box of the {obj1} less than the one of the {obj2}? Select "yes" or "no" as the answer.
""".strip()

OBJ_COUNT_TEMPLATE = """
Please count the number of {obj1} in the room. Give a number as the answer.
""".strip()