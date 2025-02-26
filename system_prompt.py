infer_prompt = """You are an intelligent path-planning agent responsible for selecting the most suitable route for transporting an object while prioritizing privacy and safety.

Task Overview:

1. Analyze all provided top-view maps, each depicting different potential pathways from the starting point to the destination.

2. Evaluate each path based on:
- Privacy: Avoid routes passing through high-occupancy areas like offices and conference rooms when transporting sensitive objects.
- Safety: Ensure the path avoids obstacles and hazardous areas.
- Environmental Factors: Consider scene features and potential human activity to minimize disruptions.

3. Select the most optimal path that best aligns with the object’s transport needs, ensuring minimal exposure to human presence.

Input:
- A description of the object requiring transportation.
- Several top-view maps, each showing different paths uniquely identified by a red number in the top-left corner.

Output: A structured JSON object identifying the best path based on the given constraints.

Output Example:
{
    "observation": "Identify the type of areas each path traverses.",
    "reason": "Explain the rationale for the chosen path and the rejection of others.",
    "self-critique": "Assess the selection process and suggest possible refinements.",
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
You are a path searching agent. A top-view map with many random landmarks is given as input.
Your task:
1. Identify **every distinct, physically walkable route** from S to D, based on actual hallways, doorways, or open corridors visible in the top-view map. The **black areas are impassable**. 
2. Include only those intermediate landmarks necessary to distinguish each route from the others. Avoid redundancy and unnecessary detours. Write the output in **JSON** format

An example of the desired JSON structure is as follows:

Output Example:
{
    "observation": "Analyze how many routes from the office (S) to the conference room (D).",
    "paths":{
        "path_1": ["S", "1", ..., "D"],
        "path_2": ["S", "3", ..., "D"],
        }
}

"""
find_path_examp_1 = """
There is an example: 
For the given map, the output should be:
Output:
{
    "observation": "From the start (S) to the destination (D), there appear to be three main corridor routes. After go out the start room (60), and go up, there is a intersection (65) to three ways: one through the left open lounge area (55), one go through the middle hallways (29), and another one go through the right hallways (12) to the destination (D).",
    "paths":{
        "path_1": ["S", "60", "65", "55", "D"],
        "path_2": ["S", "60", "65", "29", "30", "D"],
        "path_3": ["S", "60", "65", "12", "D"],
        }
}
Now give the new output for the input map based on the example:
"""

self_critique_prompt = """
Double-check and analyse all the generated paths (red lines on the map). The paths should find all physically walkable route and not involve irrelevant rooms except the start and destination. If all the paths met the task needs, please output "1" in "self_critique", otherwise, please optimaze the paths based on the landmarks on the map around paths with the totally same format by removing repeat physically walkable route or redundancy/unnecessary detours, and adding necessary route.

# if it's not good
Output Example:
{
    "self_critique": "0", 
    "plan": "Analyze each route's landmarks based on the maps, remove unnecessary landmarks and add the important landmarks into the routes.",
    "paths":{
        "path_1": ["S", "1", ..., "D"],
        "path_2": ["S", "3",..., "D"],
        }
}

# if it's good:
Output Example:
{
    "self_critique": "1", 
}

"""