
# Example.py
QA_FEW_SHOT = """
Example 1 (Global Object Count):
Q: Are there at least 3 meeting_chair(s) in this room?
A: Yes
"""
# Example 1 (Object Counting):
# Q: How many beds are in the given scene?
# A: 1

# Example 2 (Object Proximity Comparison): 
# Q: Measuring from the closest point of each object, which of these objects (refrigerator, sofa, ceiling light, cutting board) is the closest to the printer? 
# A. refrigerator 
# B. sofa 
# C. ceiling light 
# D. cutting board
# A: D. cutting board
# QA_FEW_SHOT = """
# Example 11 (Object Count):
# Q: How many chairs are there in this room?
# A: 4
# (Logic Hint: Count all detected instances with category == "chair". Return the integer count.)

# Example 12 (Relative Direction):
# Q: If I am standing by the refrigerator and facing the sofa, is the kettle to my left, right, or back?
# A. left
# B. right
# C. back
# A: C. back
# (Logic Hint: Compute kettle position relative to the agent's facing vector at the specified reference viewpoint (facing the sofa). Map the relative 2D angle to {left, right, back, front} and return the closest label.)

# Example 13 (Object Size):
# Q: What is the length of the longest dimension (length, width, or height) of the refrigerator in centimeters?
# A: 119
# (Logic Hint: Extract the object's world-axis-aligned bounding box dimensions (or OBB lengths), find the maximum of the three (length/width/height), convert to centimeters, and return the numeric value.)

# Example 14 (Room Size / Area Estimation):
# Q: What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space.
# A: 57.6
# (Logic Hint: Estimate room floor polygon area in world coordinates (sum areas for multiple rooms if present). Return the area in square meters.)

# Example 15 (Object Set Verification):
# Q: Which of the following options does not contain any objects in the given scene?
# A. plant, TV, bed, cabinet
# B. lamp, carpet, TV, window
# C. door, TV, window, cabinet
# D. plant, TV, bed, window
# A: B. lamp, carpet, TV, window
# (Logic Hint: Extract the list of objects in the scene. For each option, check if the intersection between the scene's objects and the option's object list is empty. Return the option where the intersection is empty.)

# Example 16 (Object Counting):
# Q: How many beds are in the given scene?
# A. 1 
# B. 2 
# C. 3 
# D. 4 
# A: A. 1
# (Logic Hint: Iterate through the objects in the scene and count the number of instances where object_class == "bed". Return the option that matches this count.)

# Example 17 (Dimensional Comparison):
# Q: Which description is correct?
# A. The door is lower than the bed.
# B. The door is wider than the TV.
# C. The lamp is taller than the bed.
# D. The plant is lower than the bed.
# A: C. The lamp is taller than the bed.
# (Logic Hint: Retrieve the 3D bounding box dimensions for the objects in each option. Evaluate the comparative logic (e.g., height(door) < height(bed) or width(door) > width(TV)). Return the option that evaluates to True.)

# Example 18 (Viewpoint-based Spatial Relation):
# Q: When viewing from the entrance, which descriptions are correct?
# A. Bed is on the center of the room. 
# B. TV is on the left side of the room.
# C. The cabinet is the farthest object that can be seen.
# D. Bed is on the right side of the room
# A: D. Bed is on the right side of the room
# (Logic Hint: Establish a local coordinate system with the origin at the entrance, facing into the room. Evaluate the relative positions (x-axis for left/right/center) and depth (y/z-axis for farthest) of the specified objects. Return the correct option.)

# Example 19 (Room Type Identification):
# Q: Which room is this?
# A: Bedroom
# (Logic Hint: Access the `object_name` or `id` attribute of any object in the scene dictionary. Parse the string to extract the text enclosed in parentheses at the very end (e.g., extract "medium-sized meeting room" from "magazine-0|side_table-0 (medium-sized meeting room)"). Format and return this extracted string as the room type.)

# Example 20 (Object Existence):
# Q: Is there a sofa in the scene?
# A: Yes
# (Logic Hint: Iterate through all valid objects in the scene's bounding box dictionary. Check if any object's `category` exactly matches or contains the target parameter (e.g., "sofa"). Return "Yes" if at least one match is found, otherwise return "No".)
# """


# QA_FEW_SHOT = """
# Example 1 (Global Object Count):
# Q: Are there at least 3 meeting_chair(s) in this room?
# A: Yes
# (Logic Hint: Check if object_counts[category] >= count. Both category and count are parameters.)
# Example 2 (Global Object Count):
# Q: Are there at least 2 meeting chair(s) in this room?
# A: No
# (Logic Hint: Check if object_counts[category] >= count. Both category and count are parameters.)

# Example 3 (Object Count):
# Q: How many chairs are there in this room?
# A: 4
# (Logic Hint: Count all detected instances with category == "chair". Return the integer count.)

# Example 4 (Object Size):
# Q: What is the length of the longest dimension (length, width, or height) of the refrigerator in centimeters?
# A: 119
# (Logic Hint: Extract the object's world-axis-aligned bounding box dimensions (or OBB lengths), find the maximum of the three (length/width/height), convert to centimeters, and return the numeric value.)

# Example 5 (Room Size / Area Estimation):
# Q: What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space.
# A: 57.6
# (Logic Hint: Estimate room floor polygon area in world coordinates (sum areas for multiple rooms if present). Return the area in square meters.)

# Example 6 (Object Proximity Comparison): 
# Q: Measuring from the closest point of each object, which of these objects (refrigerator, sofa, ceiling light, cutting board) is the closest to the printer? 
# A. refrigerator 
# B. sofa 
# C. ceiling light 
# D. cutting board
# A: D. cutting board
# (Logic Hint: Calculate distance(printer, candidate) for each candidate in the list. Return the candidate with the minimum distance value.)

# Example 7 (Object Proximity Comparison):
# Q: Measuring from the closest point of each object, which of these objects (kettle, toaster, cutting board, refrigerator) is the closest to the microwave?
# A. kettle
# B. toaster
# C. cutting board
# D. refrigerator
# A: B. toaster
# (Logic Hint: Calculate distance(microwave, candidate) for each candidate in the list. Return the candidate with the minimum distance value.)

# Example 8 (Object Distance Measurement):
# Q: Measuring from the closest point of each object, what is the distance between the bed and the sofa in meters?
# A: [numeric_value]
# (Logic Hint: Compute distance(bed, sofa) using the minimum point-to-point distance between their bounding volumes. Return the distance value in meters.)

# Example 9 (Global Object Count):
# Q: Are there at least 3 meeting_chair(s) in this room?
# A: Yes
# (Logic Hint: Check if object_counts[category] >= count. Both category and count are parameters.)

# Example 10 (Global Object Count):
# Q: Are there at least 2 meeting chair(s) in this room?
# A: No
# (Logic Hint: Check if object_counts[category] >= count. Both category and count are parameters.)
# """

# Example 11 (Object Count):
# Q: How many chairs are there in this room?
# A: 4
# (Logic Hint: Count all detected instances with category == "chair". Return the integer count.)

# Example 12 (Relative Direction):
# Q: If I am standing by the refrigerator and facing the sofa, is the kettle to my left, right, or back?
# A. left
# B. right
# C. back
# A: C. back
# (Logic Hint: Compute kettle position relative to the agent's facing vector at the specified reference viewpoint (facing the sofa). Map the relative 2D angle to {left, right, back, front} and return the closest label.)

# Example 13 (Object Size):
# Q: What is the length of the longest dimension (length, width, or height) of the refrigerator in centimeters?
# A: 119
# (Logic Hint: Extract the object's world-axis-aligned bounding box dimensions (or OBB lengths), find the maximum of the three (length/width/height), convert to centimeters, and return the numeric value.)

# Example 14 (Room Size / Area Estimation):
# Q: What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space.
# A: 57.6
# (Logic Hint: Estimate room floor polygon area in world coordinates (sum areas for multiple rooms if present). Return the area in square meters.)

# Example 15 (Object Set Verification):
# Q: Which of the following options does not contain any objects in the given scene?
# A. plant, TV, bed, cabinet
# B. lamp, carpet, TV, window
# C. door, TV, window, cabinet
# D. plant, TV, bed, window
# A: B. lamp, carpet, TV, window
# (Logic Hint: Extract the list of objects in the scene. For each option, check if the intersection between the scene's objects and the option's object list is empty. Return the option where the intersection is empty.)

# Example 16 (Object Counting):
# Q: How many beds are in the given scene?
# A. 1 
# B. 2 
# C. 3 
# D. 4 
# A: A. 1
# (Logic Hint: Iterate through the objects in the scene and count the number of instances where object_class == "bed". Return the option that matches this count.)

# Example 17 (Dimensional Comparison):
# Q: Which description is correct?
# A. The door is lower than the bed.
# B. The door is wider than the TV.
# C. The lamp is taller than the bed.
# D. The plant is lower than the bed.
# A: C. The lamp is taller than the bed.
# (Logic Hint: Retrieve the 3D bounding box dimensions for the objects in each option. Evaluate the comparative logic (e.g., height(door) < height(bed) or width(door) > width(TV)). Return the option that evaluates to True.)

# Example 18 (Viewpoint-based Spatial Relation):
# Q: When viewing from the entrance, which descriptions are correct?
# A. Bed is on the center of the room. 
# B. TV is on the left side of the room.
# C. The cabinet is the farthest object that can be seen.
# D. Bed is on the right side of the room
# A: D. Bed is on the right side of the room
# (Logic Hint: Establish a local coordinate system with the origin at the entrance, facing into the room. Evaluate the relative positions (x-axis for left/right/center) and depth (y/z-axis for farthest) of the specified objects. Return the correct option.)

# Example 19 (Room Type Identification):
# Q: Which room is this?
# A: Bedroom
# (Logic Hint: Access the `object_name` or `id` attribute of any object in the scene dictionary. Parse the string to extract the text enclosed in parentheses at the very end (e.g., extract "medium-sized meeting room" from "magazine-0|side_table-0 (medium-sized meeting room)"). Format and return this extracted string as the room type.)

# Example 20 (Object Existence):
# Q: Is there a sofa in the scene?
# A: Yes
# (Logic Hint: Iterate through all valid objects in the scene's bounding box dictionary. Check if any object's `category` exactly matches or contains the target parameter (e.g., "sofa"). Return "Yes" if at least one match is found, otherwise return "No".)

# Example 21 (Egocentric Proximity):
# Q: Which object appears closest to you?
# A: Chair
# (Logic Hint: Retrieve the camera/agent's current 3D position from the view metadata. Calculate the Euclidean distance between the camera's position and the closest point of the bounding box (using `min`/`max`) for every visible object in the scene. Return the `category` of the object with the absolute minimum distance.)

# Example 22 (Fact Validation - Count Comparison):
# Q: Are there fewer chairs than tables? Please reply with a "yes" or "no" only.
# A: yes
# (Logic Hint: Iterate through the valid objects and count the instances of {obj1} (e.g., "chair") and {obj2} (e.g., "table"). Evaluate the boolean condition `count(obj1) < count(obj2)`. Return "yes" if the condition is true, otherwise "no".)

# Example 23 (Fact Validation - Distance Comparison):
# Q: Is the distance between the sofa and the TV greater than the distance between the bed and the wardrobe?
# A: no
# (Logic Hint: Calculate the minimum bounding box distance `d1` between {obj1} (sofa) and {obj2} (TV). Calculate the minimum bounding box distance `d2` between {obj3} (bed) and {obj4} (wardrobe). Evaluate the boolean condition `d1 > d2`. Return "yes" if true, otherwise "no".)

# Example 24 (Fact Validation - Size Comparison):
# Q: Is the size of the bounding box of the refrigerator less than the one of the oven? Select "yes" or "no" as the answer.
# A: yes
# (Logic Hint: Retrieve the 3D bounding box dimensions for {obj1} and {obj2}. Calculate their respective bounding box volumes (length * width * height). Evaluate the boolean condition `volume(obj1) < volume(obj2)`. Return "yes" if true, otherwise "no".)

# Example 25 (Spatial Relation - Relative Direction MCQ):
# Q: What is to the left of the {obj1}? A) Armchair B) Bookshelf C) Lamp D) Painting E) Couch
# A: E
# (Logic Hint: Determine the forward-facing vector of {obj1}. Calculate the relative vectors to other objects on the XZ plane. Use dot/cross products or planar angles to find which object falls squarely in the "left" directional cone. Map the found category to its corresponding multiple-choice letter.)
# """
# # QA_FEW_SHOT = """
# Example 26 (Counting & Existence - Exact Count):
# Q: Please count the number of {obj1} in the room. Give a number as the answer.
# A: 2
# (Logic Hint: Iterate through all items in `valid_objects_dict`. Increment a counter each time an object's category exactly matches {obj1}. Return the final integer count as a string.)

# Example 27 (Distance Measurement - Exact Distance):
# Q: Please estimate the distance between the {obj1} and {obj2} in the room in meters. Give a numerical response.
# A: 1.04
# (Logic Hint: Retrieve the bounding boxes for {obj1} and {obj2}. Calculate the minimum Euclidean distance between their Axis-Aligned Bounding Boxes (AABB). Format the resulting float to two decimal places.)

# Example 28 (Object Property - Volume Estimation):
# Q: Can you estimate the volume of the bounding box of {obj1} in cubic meters? Give a numerical response.
# A: 3.83
# (Logic Hint: Retrieve the `min` and `max` bounds for {obj1}. Calculate its dimensions (max - min) and multiply length, width, and height to get the volume. Format the float result to two decimal places.)

# Example 29 (Spatial Relation - Complex Relative Direction):
# Q: If I am standing by the {obj1} and facing the closest {obj2}, is the closest {obj3} to my front, back, left, right, front-left, front-right, back-left, or back-right in this room?
# A: front-right
# (Logic Hint: Establish the origin at the centroid of {obj1}. Compute the forward view vector extending from {obj1} to {obj2}. Compute the target vector from {obj1} to {obj3}. Project both vectors onto the XZ plane. Calculate the planar angle between them to categorize the target into one of the 8 directional bins.)

# Example 30 (Proximity Comparison - Closest among Candidates):
# Q: Measuring from the closest point of each object, which of these objects ({opt_a}, {opt_b}, {opt_c}, {opt_d}) is the closest to the {obj1} in this room?
# A: stool
# (Logic Hint: Retrieve the bounding boxes for the reference {obj1} and all candidate objects provided in the options. For each candidate, calculate the minimum bounding box distance (AABB distance) to {obj1}. Return the exact name of the candidate with the smallest distance.)

# Example 31 (Spatial Relation - Negative Sampling):
# Q: If I am standing by the {obj1} and facing the closest {obj2}, is the closest {obj3} to my front, back, left, right, front-left, front-right, back-left, or back-right in this PANORAMA?
# A: The orienting object or querying object is not found in the picture.
# (Logic Hint: Intentionally sample {obj1}, {obj2}, or {obj3} from a global vocabulary such that at least one object does NOT exist in `valid_objects_dict`. When the existence check fails, immediately bypass all spatial math and return the strict fallback string: "The orienting object or querying object is not found in the picture.")

# Example 32 (Proximity Comparison - Negative Sampling):
# Q: Measuring from the closest point of each object, which of these objects ({opt_a}, {opt_b}, {opt_c}) is the closest to the {obj1} in this PANORAMA?
# A: None of the candidates were found in the picture.
# (Logic Hint: Intentionally sample the candidate options ({opt_a}, {opt_b}, {opt_c}) from a disjoint vocabulary list that does not overlap with any object categories present in the scene. Upon confirming that none of the candidate objects exist in `valid_objects_dict`, skip the distance calculations and return the strict fallback string: "None of the candidates were found in the picture.")
# """
# QA_FEW_SHOT = """
# Example 16 (Object Counting):
# Q: How many beds are in the given scene?
# A. 1 
# B. 2 
# C. 3 
# D. 4 
# A: A. 1
# (Logic Hint: Iterate through the objects in the scene and count the number of instances where object_class == "bed". Return the option that matches this count.)

# Example 17 (Dimensional Comparison):
# Q: Which description is correct?
# A. The door is lower than the bed.
# B. The door is wider than the TV.
# C. The lamp is taller than the bed.
# D. The plant is lower than the bed.
# A: C. The lamp is taller than the bed.
# (Logic Hint: Retrieve the 3D bounding box dimensions for the objects in each option. Evaluate the comparative logic (e.g., height(door) < height(bed) or width(door) > width(TV)). Return the option that evaluates to True.)

# Example 18 (Viewpoint-based Spatial Relation):
# Q: When viewing from the entrance, which descriptions are correct?
# A. Bed is on the center of the room. 
# B. TV is on the left side of the room.
# C. The cabinet is the farthest object that can be seen.
# D. Bed is on the right side of the room
# A: D. Bed is on the right side of the room
# (Logic Hint: Establish a local coordinate system with the origin at the entrance, facing into the room. Evaluate the relative positions (x-axis for left/right/center) and depth (y/z-axis for farthest) of the specified objects. Return the correct option.)

# Example 19 (Room Type Identification):
# Q: Which room is this?
# A: Bedroom
# (Logic Hint: Access the `object_name` or `id` attribute of any object in the scene dictionary. Parse the string to extract the text enclosed in parentheses at the very end (e.g., extract "medium-sized meeting room" from "magazine-0|side_table-0 (medium-sized meeting room)"). Format and return this extracted string as the room type.)

# Example 20 (Object Existence):
# Q: Is there a sofa in the scene?
# A: Yes
# (Logic Hint: Iterate through all valid objects in the scene's bounding box dictionary. Check if any object's `category` exactly matches or contains the target parameter (e.g., "sofa"). Return "Yes" if at least one match is found, otherwise return "No".)

# Example 21 (Egocentric Proximity):
# Q: Which object appears closest to you?
# A: Chair
# (Logic Hint: Retrieve the camera/agent's current 3D position from the view metadata. Calculate the Euclidean distance between the camera's position and the closest point of the bounding box (using `min`/`max`) for every visible object in the scene. Return the `category` of the object with the absolute minimum distance.)

# Example 22 (Fact Validation - Count Comparison):
# Q: Are there fewer chairs than tables? Please reply with a "yes" or "no" only.
# A: yes
# (Logic Hint: Iterate through the valid objects and count the instances of {obj1} (e.g., "chair") and {obj2} (e.g., "table"). Evaluate the boolean condition `count(obj1) < count(obj2)`. Return "yes" if the condition is true, otherwise "no".)

# Example 23 (Fact Validation - Distance Comparison):
# Q: Is the distance between the sofa and the TV greater than the distance between the bed and the wardrobe?
# A: no
# (Logic Hint: Calculate the minimum bounding box distance `d1` between {obj1} (sofa) and {obj2} (TV). Calculate the minimum bounding box distance `d2` between {obj3} (bed) and {obj4} (wardrobe). Evaluate the boolean condition `d1 > d2`. Return "yes" if true, otherwise "no".)

# Example 24 (Fact Validation - Size Comparison):
# Q: Is the size of the bounding box of the refrigerator less than the one of the oven? Select "yes" or "no" as the answer.
# A: yes
# (Logic Hint: Retrieve the 3D bounding box dimensions for {obj1} and {obj2}. Calculate their respective bounding box volumes (length * width * height). Evaluate the boolean condition `volume(obj1) < volume(obj2)`. Return "yes" if true, otherwise "no".)

# Example 25 (Spatial Relation - Relative Direction MCQ):
# Q: What is to the left of the {obj1}? A) Armchair B) Bookshelf C) Lamp D) Painting E) Couch
# A: E
# (Logic Hint: Determine the forward-facing vector of {obj1}. Calculate the relative vectors to other objects on the XZ plane. Use dot/cross products or planar angles to find which object falls squarely in the "left" directional cone. Map the found category to its corresponding multiple-choice letter.)
# """
# QA_FEW_SHOT = """
# Example 26 (Counting & Existence - Exact Count):
# Q: Please count the number of {obj1} in the room. Give a number as the answer.
# A: 2
# (Logic Hint: Iterate through all items in `valid_objects_dict`. Increment a counter each time an object's category exactly matches {obj1}. Return the final integer count as a string.)

# Example 27 (Distance Measurement - Exact Distance):
# Q: Please estimate the distance between the {obj1} and {obj2} in the room in meters. Give a numerical response.
# A: 1.04
# (Logic Hint: Retrieve the bounding boxes for {obj1} and {obj2}. Calculate the minimum Euclidean distance between their Axis-Aligned Bounding Boxes (AABB). Format the resulting float to two decimal places.)

# Example 28 (Object Property - Volume Estimation):
# Q: Can you estimate the volume of the bounding box of {obj1} in cubic meters? Give a numerical response.
# A: 3.83
# (Logic Hint: Retrieve the `min` and `max` bounds for {obj1}. Calculate its dimensions (max - min) and multiply length, width, and height to get the volume. Format the float result to two decimal places.)

# Example 29 (Spatial Relation - Complex Relative Direction):
# Q: If I am standing by the {obj1} and facing the closest {obj2}, is the closest {obj3} to my front, back, left, right, front-left, front-right, back-left, or back-right in this room?
# A: front-right
# (Logic Hint: Establish the origin at the centroid of {obj1}. Compute the forward view vector extending from {obj1} to {obj2}. Compute the target vector from {obj1} to {obj3}. Project both vectors onto the XZ plane. Calculate the planar angle between them to categorize the target into one of the 8 directional bins.)

# Example 30 (Proximity Comparison - Closest among Candidates):
# Q: Measuring from the closest point of each object, which of these objects ({opt_a}, {opt_b}, {opt_c}, {opt_d}) is the closest to the {obj1} in this room?
# A: stool
# (Logic Hint: Retrieve the bounding boxes for the reference {obj1} and all candidate objects provided in the options. For each candidate, calculate the minimum bounding box distance (AABB distance) to {obj1}. Return the exact name of the candidate with the smallest distance.)

# Example 31 (Spatial Relation - Negative Sampling):
# Q: If I am standing by the {obj1} and facing the closest {obj2}, is the closest {obj3} to my front, back, left, right, front-left, front-right, back-left, or back-right in this PANORAMA?
# A: The orienting object or querying object is not found in the picture.
# (Logic Hint: Intentionally sample {obj1}, {obj2}, or {obj3} from a global vocabulary such that at least one object does NOT exist in `valid_objects_dict`. When the existence check fails, immediately bypass all spatial math and return the strict fallback string: "The orienting object or querying object is not found in the picture.")

# Example 32 (Proximity Comparison - Negative Sampling):
# Q: Measuring from the closest point of each object, which of these objects ({opt_a}, {opt_b}, {opt_c}) is the closest to the {obj1} in this PANORAMA?
# A: None of the candidates were found in the picture.
# (Logic Hint: Intentionally sample the candidate options ({opt_a}, {opt_b}, {opt_c}) from a disjoint vocabulary list that does not overlap with any object categories present in the scene. Upon confirming that none of the candidate objects exist in `valid_objects_dict`, skip the distance calculations and return the strict fallback string: "None of the candidates were found in the picture.")
# """
# QA_FEW_SHOT = """
# Example 1 (Global Object Count):
# Q: Are there at least 3 meeting_chair(s) in this room?
# A: Yes
# (Logic Hint: Check if object_counts[category] >= count. Both category and count are parameters.)

# Example 2 (Global Object Count):
# Q: Are there at least 2 meeting chair(s) in this room?
# A: No
# (Logic Hint: Check if object_counts[category] >= count. Both category and count are parameters.)

# Example 3 (Object Count):
# Q: How many chairs are there in this room?
# A: 4
# (Logic Hint: Count all detected instances with category == "chair". Return the integer count.)

# Example 4 (Object Size):
# Q: What is the length of the longest dimension (length, width, or height) of the refrigerator in centimeters?
# A: 119
# (Logic Hint: Extract the object's world-axis-aligned bounding box dimensions (or OBB lengths), find the maximum of the three (length/width/height), convert to centimeters, and return the numeric value.)

# Example 5 (Room Size / Area Estimation):
# Q: What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space.
# A: 57.6
# (Logic Hint: Estimate room floor polygon area in world coordinates (sum areas for multiple rooms if present). Return the area in square meters.)
# """

# QA_FEW_SHOT = """
# Example 1 (Object Proximity Comparison): 
# Q: Measuring from the closest point of each object, which of these objects (refrigerator, sofa, ceiling light, cutting board) is the closest to the printer? 
# A. refrigerator 
# B. sofa 
# C. ceiling light 
# D. cutting board
# A: D. cutting board
# (Logic Hint: Calculate distance(printer, candidate) for each candidate in the list. Return the candidate with the minimum distance value.)

# Example 2 (Object Proximity Comparison):
# Q: Measuring from the closest point of each object, which of these objects (kettle, toaster, cutting board, refrigerator) is the closest to the microwave?
# A. kettle
# B. toaster
# C. cutting board
# D. refrigerator
# A: B. toaster
# (Logic Hint: Calculate distance(microwave, candidate) for each candidate in the list. Return the candidate with the minimum distance value.)

# Example 3 (Object Distance Measurement):
# Q: Measuring from the closest point of each object, what is the distance between the bed and the sofa in meters?
# A: [numeric_value]
# (Logic Hint: Compute distance(bed, sofa) using the minimum point-to-point distance between their bounding volumes. Return the distance value in meters.)

# Example 4 (Global Object Count):
# Q: Are there at least 3 meeting_chair(s) in this room?
# A: Yes
# (Logic Hint: Check if object_counts[category] >= count. Both category and count are parameters.)

# Example 5 (Global Object Count):
# Q: Are there at least 2 meeting chair(s) in this room?
# A: No
# (Logic Hint: Check if object_counts[category] >= count. Both category and count are parameters.)

# Example 6 (Object Count):
# Q: How many chairs are there in this room?
# A: 4
# (Logic Hint: Count all detected instances with category == "chair". Return the integer count.)

# Example 7 (Relative Direction):
# Q: If I am standing by the refrigerator and facing the sofa, is the kettle to my left, right, or back?
# A. left
# B. right
# C. back
# A: C. back
# (Logic Hint: Compute kettle position relative to the agent's facing vector at the specified reference viewpoint (facing the sofa). Map the relative 2D angle to {left, right, back, front} and return the closest label.)

# Example 8 (Object Size):
# Q: What is the length of the longest dimension (length, width, or height) of the refrigerator in centimeters?
# A: 119
# (Logic Hint: Extract the object's world-axis-aligned bounding box dimensions (or OBB lengths), find the maximum of the three (length/width/height), convert to centimeters, and return the numeric value.)

# Example 9 (Room Size / Area Estimation):
# Q: What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space.
# A: 57.6
# (Logic Hint: Estimate room floor polygon area in world coordinates (sum areas for multiple rooms if present). Return the area in square meters.)
# """

# QA_FEW_SHOT = """
# Example 1 (Object Set Verification):
# Q: Which of the following options does not contain any objects in the given scene?
# A. plant, TV, bed, cabinet
# B. lamp, carpet, TV, window
# C. door, TV, window, cabinet
# D. plant, TV, bed, window
# A: B. lamp, carpet, TV, window
# (Logic Hint: Extract the list of objects in the scene. For each option, check if the intersection between the scene's objects and the option's object list is empty. Return the option where the intersection is empty.)

# Example 2 (Object Counting):
# Q: How many beds are in the given scene?
# A. 1 
# B. 2 
# C. 3 
# D. 4 
# A: A. 1
# (Logic Hint: Iterate through the objects in the scene and count the number of instances where object_class == "bed". Return the option that matches this count.)

# Example 3 (Dimensional Comparison):
# Q: Which description is correct?
# A. The door is lower than the bed.
# B. The door is wider than the TV.
# C. The lamp is taller than the bed.
# D. The plant is lower than the bed.
# A: C. The lamp is taller than the bed.
# (Logic Hint: Retrieve the 3D bounding box dimensions for the objects in each option. Evaluate the comparative logic (e.g., height(door) < height(bed) or width(door) > width(TV)). Return the option that evaluates to True.)

# Example 4 (Viewpoint-based Spatial Relation):
# Q: When viewing from the entrance, which descriptions are correct?
# A. Bed is on the center of the room. 
# B. TV is on the left side of the room.
# C. The cabinet is the farthest object that can be seen.
# D. Bed is on the right side of the room
# A: D. Bed is on the right side of the room
# (Logic Hint: Establish a local coordinate system with the origin at the entrance, facing into the room. Evaluate the relative positions (x-axis for left/right/center) and depth (y/z-axis for farthest) of the specified objects. Return the correct option.)
# """

# QA_FEW_SHOT = """
# Example 1 (Room Type Identification):
# Q: Which room is this?
# A: Bedroom
# (Logic Hint: Access the `object_name` or `id` attribute of any object in the scene dictionary. Parse the string to extract the text enclosed in parentheses at the very end (e.g., extract "medium-sized meeting room" from "magazine-0|side_table-0 (medium-sized meeting room)"). Format and return this extracted string as the room type.)

# Example 2 (Object Existence):
# Q: Is there a sofa in the scene?
# A: Yes
# (Logic Hint: Iterate through all valid objects in the scene's bounding box dictionary. Check if any object's `category` exactly matches or contains the target parameter (e.g., "sofa"). Return "Yes" if at least one match is found, otherwise return "No".)

# Example 3 (Egocentric Proximity):
# Q: Which object appears closest to you?
# A: Chair
# (Logic Hint: Retrieve the camera/agent's current 3D position from the view metadata. Calculate the Euclidean distance between the camera's position and the closest point of the bounding box (using `min`/`max`) for every visible object in the scene. Return the `category` of the object with the absolute minimum distance.)
# """

# QA_FEW_SHOT = """
# Example 1 (Fact Validation - Count Comparison):
# Q: Are there fewer chairs than tables? Please reply with a "yes" or "no" only.
# A: yes
# (Logic Hint: Iterate through the valid objects and count the instances of {obj1} (e.g., "chair") and {obj2} (e.g., "table"). Evaluate the boolean condition `count(obj1) < count(obj2)`. Return "yes" if the condition is true, otherwise "no".)

# Example 2 (Fact Validation - Distance Comparison):
# Q: Is the distance between the sofa and the TV greater than the distance between the bed and the wardrobe?
# A: no
# (Logic Hint: Calculate the minimum bounding box distance `d1` between {obj1} (sofa) and {obj2} (TV). Calculate the minimum bounding box distance `d2` between {obj3} (bed) and {obj4} (wardrobe). Evaluate the boolean condition `d1 > d2`. Return "yes" if true, otherwise "no".)

# Example 3 (Fact Validation - Size Comparison):
# Q: Is the size of the bounding box of the refrigerator less than the one of the oven? Select "yes" or "no" as the answer.
# A: yes
# (Logic Hint: Retrieve the 3D bounding box dimensions for {obj1} and {obj2}. Calculate their respective bounding box volumes (length * width * height). Evaluate the boolean condition `volume(obj1) < volume(obj2)`. Return "yes" if true, otherwise "no".)
# """

# QA_FEW_SHOT = """
# Example 4 (Spatial Relation - Relative Direction MCQ):
# Q: What is to the left of the {obj1}? A) Armchair B) Bookshelf C) Lamp D) Painting E) Couch
# A: E
# (Logic Hint: Determine the forward-facing vector of {obj1}. Calculate the relative vectors to other objects on the XZ plane. Use dot/cross products or planar angles to find which object falls squarely in the "left" directional cone. Map the found category to its corresponding multiple-choice letter.)

# Example 5 (Counting & Existence - Exact Count):
# Q: Please count the number of {obj1} in the room. Give a number as the answer.
# A: 2
# (Logic Hint: Iterate through all items in `valid_objects_dict`. Increment a counter each time an object's category exactly matches {obj1}. Return the final integer count as a string.)

# Example 6 (Distance Measurement - Exact Distance):
# Q: Please estimate the distance between the {obj1} and {obj2} in the room in meters. Give a numerical response.
# A: 1.04
# (Logic Hint: Retrieve the bounding boxes for {obj1} and {obj2}. Calculate the minimum Euclidean distance between their Axis-Aligned Bounding Boxes (AABB). Format the resulting float to two decimal places.)

# Example 7 (Object Property - Volume Estimation):
# Q: Can you estimate the volume of the bounding box of {obj1} in cubic meters? Give a numerical response.
# A: 3.83
# (Logic Hint: Retrieve the `min` and `max` bounds for {obj1}. Calculate its dimensions (max - min) and multiply length, width, and height to get the volume. Format the float result to two decimal places.)
# """

# QA_FEW_SHOT = """
# Example 8 (Spatial Relation - Complex Relative Direction):
# Q: If I am standing by the {obj1} and facing the closest {obj2}, is the closest {obj3} to my front, back, left, right, front-left, front-right, back-left, or back-right in this room?
# A: front-right
# (Logic Hint: Establish the origin at the centroid of {obj1}. Compute the forward view vector extending from {obj1} to {obj2}. Compute the target vector from {obj1} to {obj3}. Project both vectors onto the XZ plane. Calculate the planar angle between them to categorize the target into one of the 8 directional bins.)

# Example 9 (Proximity Comparison - Closest among Candidates):
# Q: Measuring from the closest point of each object, which of these objects ({opt_a}, {opt_b}, {opt_c}, {opt_d}) is the closest to the {obj1} in this room?
# A: stool
# (Logic Hint: Retrieve the bounding boxes for the reference {obj1} and all candidate objects provided in the options. For each candidate, calculate the minimum bounding box distance (AABB distance) to {obj1}. Return the exact name of the candidate with the smallest distance.)
# """

# QA_FEW_SHOT = """
# Example 10 (Spatial Relation - Negative Sampling):
# Q: If I am standing by the {obj1} and facing the closest {obj2}, is the closest {obj3} to my front, back, left, right, front-left, front-right, back-left, or back-right in this PANORAMA?
# A: The orienting object or querying object is not found in the picture.
# (Logic Hint: Intentionally sample {obj1}, {obj2}, or {obj3} from a global vocabulary such that at least one object does NOT exist in `valid_objects_dict`. When the existence check fails, immediately bypass all spatial math and return the strict fallback string: "The orienting object or querying object is not found in the picture.")

# Example 11 (Proximity Comparison - Negative Sampling):
# Q: Measuring from the closest point of each object, which of these objects ({opt_a}, {opt_b}, {opt_c}) is the closest to the {obj1} in this PANORAMA?
# A: None of the candidates were found in the picture.
# (Logic Hint: Intentionally sample the candidate options ({opt_a}, {opt_b}, {opt_c}) from a disjoint vocabulary list that does not overlap with any object categories present in the scene. Upon confirming that none of the candidate objects exist in `valid_objects_dict`, skip the distance calculations and return the strict fallback string: "None of the candidates were found in the picture.")
# """