import cv2
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from astar import AStar

from PIL import Image, ImageDraw, ImageFont

def write_number(image, number):
    
    pil_image = Image.fromarray(image)
        
    # add the number on the image
    # Initialize drawing context
    draw = ImageDraw.Draw(pil_image)
    # Define the text to be added and its position
    font_size = 80

    try:
        # Attempt to use a truetype font if available
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        # If the truetype font is not available, use the default PIL font
        font = ImageFont.load_default(font_size)

    # Calculate text size to center it
    # bbox = draw.textbbox((0, 0), text, font=font)
    text_width = 60
    text_height = 90
    padding = 3
    position = (3, 3)  # Adjust position as needed

    # Define the rectangle coordinates
    rect_x0 = position[0] - padding
    rect_y0 = position[1] - padding
    rect_x1 = position[0] + text_width + padding
    rect_y1 = position[1] + text_height + padding

    # Draw the white rectangle
    draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill="white")

    # Add text to image
    draw.text(position, str(number), fill="red", font=font)
    
    return pil_image

def write_number_for_large(image, number):
    
    pil_image = Image.fromarray(image)
        
    # add the number on the image
    # Initialize drawing context
    draw = ImageDraw.Draw(pil_image)
    # Define the text to be added and its position
    font_size = 160

    try:
        # Attempt to use a truetype font if available
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        # If the truetype font is not available, use the default PIL font
        font = ImageFont.load_default(font_size)

    # Calculate text size to center it
    # bbox = draw.textbbox((0, 0), text, font=font)
    text_width = 120
    text_height = 180
    padding = 3
    position = (3, 3)  # Adjust position as needed

    # Define the rectangle coordinates
    rect_x0 = position[0] - padding
    rect_y0 = position[1] - padding
    rect_x1 = position[0] + text_width + padding
    rect_y1 = position[1] + text_height + padding

    # Draw the white rectangle
    draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill="white")

    # Add text to image
    draw.text(position, str(number), fill="red", font=font)
    
    return pil_image

def write_scene_name(image, centers):
    
    pil_image = Image.fromarray(image)
        
    # add the number on the image
    # Initialize drawing context
    draw = ImageDraw.Draw(pil_image)
    # Define the text to be added and its position
    font_size = 40

    try:
        # Attempt to use a truetype font if available
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        # If the truetype font is not available, use the default PIL font
        font = ImageFont.load_default(font_size)

    # Add text to image
    for name, pos in centers.items():
        if "hallway" not in name:
            draw.text((pos[1], pos[0]), name, fill="red", font=font)
    
    return pil_image

def graph_show(G):
    pos = nx.spring_layout(G)  # positions for all nodes

    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=700,  width=6, edge_cmap=plt.cm.Blues)
    plt.show()
    
def clean_point_around(sx, sy, size, map):
    for i in range(sx-size, sx+size):
        for j in range(sy-size, sy+size):
            map[i, j] = 0
    return map

def is_full_containment(list1, list2):
    if len(list1) == 2:
        return False
    # 将两个列表转换为集合
    set1 = set(list1)
    set2 = set(list2)
    
    # 检查 set1 是否是 set2 的子集
    return set1.issubset(set2)

def get_all_simple_paths(G, source_node, target_node):
    # find all paths
    all_topo_paths = list(nx.all_simple_paths(G, source=source_node, target=target_node))
    print("All paths from node", source_node, "to node", target_node, ":")
    # delete the start and end points, also the room during the path
    for topo_path in all_topo_paths:         
        # print(len(topo_path), topo_path)
        if len(topo_path) == 3:
            if "WC" in topo_path[-1] or "office" in topo_path[-1] or "conference" in topo_path[-1]:
                del topo_path[-2]
        if len(topo_path) > 3:
            if "WC" in topo_path[-1] or "office" in topo_path[-1] or "conference" in topo_path[-1]:
                del topo_path[-2]
            if "WC" in topo_path[-1] or "office" in topo_path[0] or "conference" in topo_path[0]:
                del topo_path[1]
            
        if len(topo_path) > 2:
            for i in reversed(range(1, len(topo_path)-1)):
                if "office" in topo_path[i] or "conference" in topo_path[i] or "WC" in topo_path[i] or "storage" in topo_path[i] or "lobby" in topo_path[i]:
                    del topo_path[i]

    # record the lenth of path
    distance_topo_path = []
    for topo_path in all_topo_paths:  
        distance_topo_path.append(len(topo_path))
        # print(len(topo_path), topo_path)
        
    # delete similar paths
    indices = np.argsort(distance_topo_path) 
    order_list = [all_topo_paths[i] for i in indices]
    # delete similar paths
    unique_list = []  # 用来保存那些将被保留的路径
    seen_paths = set()  # 记录已经处理过的路径

    for current_path in order_list:
        if not any(is_full_containment(kept_path, current_path) for kept_path in unique_list):
            unique_list.append(current_path)  # 保留这条路径
        seen_paths.add(tuple(current_path))  

    # for topo_path in unique_list:         
    #     if len(topo_path) > 3:
    #         del topo_path[-2]
    #         del topo_path[1]
    #     elif len(topo_path) == 3:
    #         del topo_path[-2]

    # update the lenth of path            
    distance_topo_path = []
    for topo_path in unique_list:  
        distance_topo_path.append(len(topo_path))
        print(len(topo_path), topo_path)
        
    print(len(unique_list))
    if len(distance_topo_path) > 5:
        indices = np.argsort(distance_topo_path)[:5] 

        unique_list = [unique_list[i] for i in indices]
        print(unique_list)
        

        
    return unique_list

def path_plan_from_topo_graph(all_topo_paths, obstacle_map, all_centers):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(30, 30))
    ob_map = cv2.dilate((obstacle_map).astype('uint8'), kernel)
    
    all_geo_paths = []
    for topo_path in all_topo_paths:
        
        print(topo_path)
        geo_path = []
        for i in range(len(topo_path)-1):
            s_start = all_centers[topo_path[i]]
            s_goal = all_centers[topo_path[i+1]]
            ob_map = clean_point_around(s_start[0], s_start[1], 25, ob_map)
            ob_map = clean_point_around(s_goal[0], s_goal[1], 25, ob_map)
            astar = AStar(s_start, s_goal, "manhattan", ob_map)
            path, visited = astar.searching()
            geo_path.extend(path)
            
        all_geo_paths.append(geo_path)
        
    return all_geo_paths

def path_plan_from_topo_graph_for_large(all_topo_paths, obstacle_map, all_centers):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(9, 9))
    ob_map = cv2.dilate((obstacle_map).astype('uint8'), kernel)
    
    all_geo_paths = []
    for topo_path in all_topo_paths:
        
        print(topo_path)
        geo_path = []
        for i in range(len(topo_path)-1):
            s_start = all_centers[topo_path[i]]
            s_goal = all_centers[topo_path[i+1]]
            ob_map = clean_point_around(s_start[0], s_start[1], 9, ob_map)
            ob_map = clean_point_around(s_goal[0], s_goal[1], 9, ob_map)
            astar = AStar(s_start, s_goal, "manhattan", ob_map)
            path, visited = astar.searching()
            geo_path.extend(path)
            
        all_geo_paths.append(geo_path)
        
    return all_geo_paths
    
def read_maps(filename):
    data = np.load("saved_maps/" + filename +'_arrays.npz', allow_pickle=True)
    
    top_view_map = data['top_view_map']
    obstacle_map = data['obstacle_map']
    all_centers = data['all_centers']
    office_obstacle_map = data['office_obstacle_map']
    G = data['graph']
    
    return top_view_map, obstacle_map, office_obstacle_map, all_centers, G

import skfmm
from numpy import ma

def get_evaulation_map(separate_obstacle_map, source_node, target_node, scene_names, sigma_d):
    
    office_obstacle_map_list = []
    full_obstacle_map_list = []
    for ob_map, name in zip(separate_obstacle_map, scene_names):
        if source_node != name and target_node != name:
            full_obstacle_map_list.append(ob_map)
            if "office" in name or "conference" in name:
                office_obstacle_map_list.append(ob_map)
        

    office_obstacle_map_array = np.array(office_obstacle_map_list)
    office_obstacle_map = np.max(office_obstacle_map_array, axis=0)
    
    full_obstacle_map_array = np.array(full_obstacle_map_list)
    full_obstacle_map = np.max(full_obstacle_map_array, axis=0)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(55, 55))
    ob_map = cv2.dilate((office_obstacle_map).astype('uint8'), kernel)
    ob_map[full_obstacle_map==0] = 0
    
    traversible_around_ma = ma.masked_values(full_obstacle_map, 0)
    traversible_around_ma[office_obstacle_map==1] = 0
    distance_field = skfmm.distance(traversible_around_ma, dx=1)
    # traversible_ma = ma.masked_values(1- office_obstacle_map, 0)
    # distance_field = skfmm.distance(1-office_obstacle_map)
    distance_field = ma.filled(distance_field, np.max(distance_field) + 1) 
    distance_field = np.max(distance_field) - distance_field
    
    max_distance = np.max(distance_field)
    mu = max_distance  # Mean at the maximum distance
    sigma = max_distance / sigma_d  # Example standard deviation

    # Gaussian function
    gaussian_modulation = np.exp(-((distance_field - mu) ** 2) / (2 * sigma ** 2))

    return gaussian_modulation

# if __name__ == "__main__":
    
#     # load the pointcloud
#     filename = '3'  
#     top_view_map, obstacle_map, office_obstacle_map, all_centers, G = read_maps(filename)
#     print("success load!")
    
#     graph_show(G)
    
#     evaluation_map = get_evaulation_map(office_obstacle_map)
    
#     # all possible topo path searching
#     source_node = "office_3"
#     target_node = "office_14"
#     all_topo_paths = list(nx.all_simple_paths(G, source=source_node, target=target_node))
#     print("All paths from node", source_node, "to node", target_node, ":")
#     for path in all_topo_paths:
#         print(path)
        
#     # path planning
#     all_geo_paths = path_plan_from_topo_graph(all_topo_paths, obstacle_map, all_centers)
    
#     # show paths in map
#     for i, geo_path in enumerate(all_geo_paths):
#         map_with_path = top_view_map.copy()
#         x_indices, y_indices = zip(*geo_path)
#         path_map = np.zeros(obstacle_map.shape)
#         path_map[x_indices, y_indices] = 1
#         kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(5, 5))
#         path_map = cv2.dilate((path_map).astype('uint8'), kernel)
#         map_with_path[path_map == 1] = [255, 0 , 0]
        
#         map_with_path = write_number(map_with_path, i)
    
#         cv2.imshow(top_view_map)
#         cv2.waitKey(1)