import mat73
import cv2
import open3d as o3d
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from astar import AStar

import os

def load_s3dis_point_cloud(file_path):
    """
    Load the S3DIS point cloud data from the given .mat file path using mat73.
    """
    data_dict = mat73.loadmat(file_path)
    
    # Explore the keys to understand the structure of your .mat file
    print("Keys in the .mat file:", list(data_dict.keys()))

    area_key = list(data_dict.keys())[0]  # Assuming 'Area_3' or similar
    area = data_dict[area_key]

    
    all_points = []
    all_colors = []
    names = []
    
    # Iterate through the Disjoint_Space structures
    for disjoint_space in area['Disjoint_Space']:
        print(f"Processing {disjoint_space['name']}...")
        points = []
        colors = []
        for i in range(len(disjoint_space['object']['points'])):
            obj_points = np.array(disjoint_space['object']['points'][i]) # Transpose to get Nx3 shape
            obj_colors = np.array(disjoint_space['object']['RGB_color'][i])/255  # Normalize to 0-1 range

            points.append(obj_points)
            colors.append(obj_colors)
        # break
        # Concatenate all points and colors
        all_points.append(np.concatenate(points, axis=0))
        all_colors.append(np.concatenate(colors, axis=0))
        names.append(disjoint_space['name'])
    
    return all_points, all_colors, names

def get_top_view_map(points, colors, scene_names, resolution=0.05):
    
    point_sum = np.concatenate(points, axis=0)
    color_sum = np.concatenate(colors, axis=0)
    scale = 1 / resolution
    
    # top-view
    mask_v = point_sum[:, 2] <= 1.5
    points_v = point_sum[mask_v]
    colors_v = color_sum[mask_v]
    
    x_v = np.rint(points_v[:, 0] * scale).astype(np.int32)
    y_v = np.rint(points_v[:, 1] * scale).astype(np.int32)
    
    # for obstacle
    mask_o = (point_sum[:, 2] <= 2.0) & (point_sum[:, 2] >1.8)
    points_o = point_sum[mask_o]
    
    x_o = np.rint(points_o[:, 0] * scale).astype(np.int32)
    y_o = np.rint(points_o[:, 1] * scale).astype(np.int32)
    
    x_min = min(x_v.min(), x_o.min())
    x_max = max(x_v.max(), x_o.max())
    y_min = min(y_v.min(), y_o.min())
    y_max = max(y_v.max(), y_o.max())
    
    x_v -= x_min
    y_v -= y_min

    # Determine the grid dimensions
    map_width = x_max - x_min + 1
    map_height = y_max - y_min + 1

    # Create an image to store RGB colors
    top_view_map = np.zeros((map_height, map_width, 3), dtype=np.uint8)
    z_buffer = np.full((map_height, map_width), -np.inf)
    # Iterate over points
    for i in range(len(points_v)):
        if points_v[i, 2] > z_buffer[y_v[i], x_v[i]]:
            z_buffer[y_v[i], x_v[i]] = points_v[i, 2]
            top_view_map[y_v[i], x_v[i]] = (colors_v[i] * 255).astype(np.uint8)
    
    # creat the obstacle map
    
    x_o -= x_min
    y_o -= y_min
    obstacle_map = np.zeros((map_height, map_width), dtype=np.uint8)
    obstacle_map[y_o, x_o] = 1
    
    gray_map_cv = cv2.cvtColor(top_view_map, cv2.COLOR_RGB2GRAY)
    obstacle_empty_map = np.zeros(obstacle_map.shape)
    obstacle_empty_map[gray_map_cv != 0] = 1
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(5, 5))
    ob_map = cv2.dilate((obstacle_empty_map).astype('uint8'), kernel)
    ob_map = cv2.erode((ob_map).astype('uint8'), kernel)

    obstacle_map[ob_map == 0] = 1
    
    
    # creat the office obstacle map
    separate_obstacle_map = []
    for i, name in enumerate(scene_names):
        mask_v = points[i][:, 2] <= 1.5
        separate_points = points[i][mask_v]
        x = np.rint(separate_points[:, 0] * scale).astype(np.int32)
        y = np.rint(separate_points[:, 1] * scale).astype(np.int32)
        x -= x_min
        y -= y_min
        obs_map = np.zeros((map_height, map_width), dtype=np.uint8)
        obs_map[y, x] = 1
        separate_obstacle_map.append(obs_map)
    
    # transfer the center 
    all_centers = {}
    for i, point in enumerate(points):
        pos = np.mean(point[:, :2], axis=0)
        pos_x = (pos[0] * scale).astype(np.int32) - x_min
        pos_y = (pos[1] * scale).astype(np.int32) - y_min
        all_centers[scene_names[i]] = (pos_y, pos_x)

    return top_view_map, obstacle_map, separate_obstacle_map, all_centers

def convert_to_o3d_point_cloud(points):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    return pcd

def calculate_nearest_point_distance(source, target):
    distance = source.compute_point_cloud_distance(target)
    return np.min(distance)

def get_topologial_map(point_list, scene_names):
    # Initialize a graph
    G = nx.Graph()

    # Add nodes to the graph
    for i in range(len(point_list)):
        G.add_node(scene_names[i])
        
    # Add edges to the graph
    print("find all the edges between rooms and hallways")
    for i in range(len(point_list)):
        for j in range(len(point_list)):
            if i != j and "hallway" not in scene_names[i] and "hallway" in scene_names[j]:
                source_pcd = convert_to_o3d_point_cloud(point_list[i])
                target_pcd = convert_to_o3d_point_cloud(point_list[j])
                distance = calculate_nearest_point_distance(source_pcd, target_pcd)
                if distance < 0.1:
                    G.add_edge(scene_names[i], scene_names[j], weight=1)
                print(distance, ", find edge: ", scene_names[i], scene_names[j])
                
    print("find all the edges between hallways and hallways")
    for i in range(len(point_list)):
        for j in range(len(point_list)):
            if i < j and "hallway" in scene_names[i] and "hallway" in scene_names[j]:
                source_pcd = convert_to_o3d_point_cloud(point_list[i])
                target_pcd = convert_to_o3d_point_cloud(point_list[j])
                distance = calculate_nearest_point_distance(source_pcd, target_pcd)
                if distance < 3.5:
                    G.add_edge(scene_names[i], scene_names[j], weight=1)
                print(distance, ", find edge: ", scene_names[i], scene_names[j])
                
    # Identify isolated nodes
    isolated_nodes = [node for node, degree in G.degree() if degree == 0]

    # Remove isolated nodes from the graph
    G.remove_nodes_from(isolated_nodes)
    
    return G

# def saved_maps(filename, top_view_map, obstacle_map, office_obstacle_map, all_centers, G):
#     print('Saving model to {}...'.format("saved_maps/"))
#     if not os.path.exists("saved_maps/"):
#         os.makedirs("saved_maps/")
#     np.savez("saved_maps/" + filename +'_arrays.npz', top_view_map=top_view_map, obstacle_map=obstacle_map, all_centers=all_centers, office_obstacle_map=office_obstacle_map, graph=G)
#     print('Finished.')
    
# # load the pointcloud
# file_path = 'data/noXYZ_area_3_no_xyz/area_3/3d/pointcloud.mat'  
# point_sum_points, point_sum_colors, scene_names = load_s3dis_point_cloud(file_path)
# print("success load!")

# top_view_map, obstacle_map, office_obstacle_map, all_centers = get_top_view_map(point_sum_points, point_sum_colors, scene_names)

# # build topo map
# G = get_topologial_map(point_sum_points, scene_names)

# saved_maps(top_view_map, obstacle_map, office_obstacle_map, all_centers, G)

