infer_prompt = """You are a mobile robot responsible for selecting the optimal path based on the attributes of the transporting objects, the features of the environment, and the influence of human activaty. 

Your task involves analyzing several top-view maps of the scene, each illustrating different potential pathways from a starting point to the destination. Your goal is to choose the optimal path that best aligns with the needs of the attributes of the special object in terms of privacy and safety, the features of the scene, and the possible influence of human activaty in the scene such as avoid passing though the office area to decrease the potential influence of the human work, apart from just considering the shortest distance. Let’s think step by step.

- Input: You will receive the description of the object needing transportation and a few top-view maps of the scene, each marked with different paths. Each path on the map is uniquely identified by a red number in the top-left corner. The black areas in the map are obstacles, which means all the paths and rooms are closed, can't be seen from outside.
- Output: Your response should be a JSON object indicating the path ID you believe is most suitable given the object’s specific requirements.

Output Example:
{
    "observation": "Analyze what kind of scenes each path pass through in the top-view maps", 
    "reason": "give the reason why select the path and why don't select other paths",
    "self-critique": "constructive self-critique",
    "path_id": "1"
}
"""


generate_path = """You are a path planing agent that responsible for selecting the optimal path based on the attributes of the transporting objects, the features of the environment, and the influence of human activaty. 

Your task involves analyzing the given top-view map of the scene with random landmarks on the map. The starting point (S) to the destination (D) are also marked on the map. Your goal is to choose the landmarks as a path from start (S) to destination (D) that best aligns with the needs of the attributes of the special object in terms of privacy and safety. Since the path is used for robot navigation, you can only choose the landmarks on the main corridors since the robot can't cross the other rooms. The black areas on the map are impassable. Let's think step by step.

- Input: You will receive the description of the object needing transportation and a top-view map of the scene which marked with random landmarks. 
- Output: Your response should be a JSON object indicating the landmark ID you believe is most suitable given the object's specific requirements.

Output format:
{
    "observation": "Analyze what kind of scenes in the top-view maps and all the possible topological paths from start to destination", 
    "plan": "find a way that best aligns with the needs of the task using the landmarks"
    "reason": "Analyze which path should be selected and why don't select other paths",
    "path": "s, ..., d"
    "self-critique": "constructive self-critique for the alignments with the nned of the task, and check the landmarks of the path quality that avoid repeating and meanless detour.",
}

There is an example: 

"""
generate_path_examp_1 = """
Example:

Input:
Instruction: send a classified file from an office to another office.
Input top-view map:

"""
generate_path_examp_2 = """
Output:
{
    "observation": "There are few office rooms, conferece rooms, bathrooms, and corridors. The start is a office, and the destination is a conference room. It looks lile there are two ways from the start to destination. The upper way would pass a large lounge and many empty corridors, the down loop path is more shorter but will pass many office areas.", 
    "plan": "I need to find a way using the landmarks on the map. I can only select the landmarks on the hallways that can be used to connect and represent the path from start to end room and avoid obstales of the wall and room.",
    "reason": "The upper way is longer than the dowm way, but pass less office and conference area, which can keep the safety and privacy of the classified file for transportation",
    "path": "s, 5, 32, 31, 15, 30, 19, d"
    "self-critique": "The chosen path minimizes exposure to potential hazards and avoids unnecessary detours, all the landmarks are in the hallways, not in the other rooms",
}

please give the output based on the following input massages:

"""

x = """
generate_path_examp_1 = """