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


generate_path = """You are a path planning agent responsible for selecting the optimal path based on the attributes of the transporting object, environmental features, and human activity influence.

Your task is to analyze a top-view map and obstacle map with random landmarks, identifying a path from start (S) to destination (D) that prioritizes privacy and safety. The robot can only navigate main corridors, avoiding black (impassable) areas and other rooms on the map. Think step by step.

- Input: A description of the object for transport and a top-view map marked with random landmarks.
- Output: A JSON object specifying the most suitable landmark path based on the object's requirements.

Output format:
{
    "observation": "Analyze what kind of scenes in the top-view maps and all the possible topological paths from start to destination", 
    "plan": "Find a path using landmarks that best meets task needs and can be navigated on the obstacle map."
    "reason": "Justify the selected path and why others were not chosen.",
    "path": "s, ..., d"
    "self-critique": "constructive self-critique for the alignments with the nned of the task, and check the landmarks of the path taht avoiding redundancy and unnecessary detours.",
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
    "observation": "There are offices, conference rooms, bathrooms, and corridors. The start is an office, and the destination is a conference room. Two possible paths exist: the upper path passes a lounge and empty corridors, while the lower loop is shorter but crosses more office areas.",
    "plan": "Use only corridor landmarks to connect start and end, avoiding obstacles.",
    "reason": "The upper path is longer but avoids office areas, ensuring privacy and security for the classified file.",
    "path": "s, 5, 32, 31, 15, 30, 19, d",
    "self-critique": "This path minimizes exposure and avoids unnecessary detours, using only corridor landmarks."

}

please give the output based on the following input massages:

"""

find_path_prompt = """
Please analyze the provided top-view map. The map has:
- A starting point labeled "S".
- A destination labeled "D".
- Various numbered landmarks.

Your task:
1. Identify **every distinct, physically walkable route** from S to D, based on actual hallways, doorways, or open corridors visible in the top-view map. The **black areas are impassable**.
   - Do not rely solely on direct or topological landmark connections; the path must be truly navigable on the map.
   - Include each physically valid path exactly once—no duplications or purely theoretical paths.

2. Write the output in **JSON** format, containing exactly two keys at the top level:
   - `"observation"`: A short sentence describing how many routes you found and any relevant note on how they were determined.
   - `"paths"`: An array of route objects, where each route object has an ordered list of the key landmarks traversed (landmarks), including S at the start and D at the end. Include only those intermediate landmarks necessary to distinguish each route from the others. Avoid redundancy and unnecessary detours.

An example of the desired JSON structure is as follows:

Output Example:
{
    "observation": "From the office (start) to the conference room (destination), there appear to be two main corridor routes: one through the larger open lounge area at the top and another along narrower hallways at the bottom.",
    "paths":{
        "path_1": ["S", "1", ..., "D"],
        "path_2": ["S", "3",..., "D"]
        }
}
Please ensure that each listed route accurately reflects a physically walkable path in the top-view map.

Please give the output following the input map:
"""

self_critique_prompt = """
Double-check and analyse all the generated paths (red lines on the map). The paths should also not involve irrelevant rooms except the start and destination. If all the paths met the task needs, please output "1" in "self_critique", otherwise, please optimaze the paths based on the landmarks on the map around paths with the totally same format by removing repeat physically walkable route or redundancy/unnecessary detours.

# if it's not good
Output Example:
{
    "self_critique": "0", 
    "paths":{
        "path_1": ["S", "1", ..., "D"],
        "path_2": ["S", "3",..., "D"]
        }
}

# if it's good:
Output Example:
{
    "self_critique": "1", 
}

"""