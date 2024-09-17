import mat73
import matplotlib.pyplot as plt
import cv2
import math
import networkx as nx
import glob
import open3d as o3d
import open3d.core as o3c
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering

import os
import numpy as np
import threading
import time
from multiprocessing import Process, Queue, set_start_method
import pickle

import importlib
import path_finding
importlib.reload(path_finding)

def load_s3dis_point_cloud(file_path):
    """
    Load the S3DIS point cloud data from the given .mat file path using mat73.
    """
    data_dict = mat73.loadmat(file_path)
    
    # Explore the keys to understand the structure of your .mat file
    print("Keys in the .mat file:", list(data_dict.keys()))

    area_key = list(data_dict.keys())[0]  # Assuming 'Area_3' or similar
    area = data_dict[area_key]

    points = []
    colors = []
    names = []

    # Iterate through the Disjoint_Space structures
    for disjoint_space in area['Disjoint_Space']:
        print(f"Processing {disjoint_space['name']}...")

        for i in range(len(disjoint_space['object']['points'])):
            obj_points = np.array(disjoint_space['object']['points'][i]) # Transpose to get Nx3 shape
            obj_colors = np.array(disjoint_space['object']['RGB_color'][i])/255  # Normalize to 0-1 range

            points.append(obj_points)
            colors.append(obj_colors)
            
        names.append(disjoint_space['name'])
        # break
    # Concatenate all points and colors
    all_points = np.concatenate(points, axis=0)
    all_colors = np.concatenate(colors, axis=0)
    
    return all_points, all_colors, names


def get_top_view_map(point_sum, color_sum, resolution=0.02):

    scale = 1 / 0.01
    # top-view
    mask_v = point_sum[:, 1] <= 1.5
    points_v = point_sum[mask_v]
    colors_v = color_sum[mask_v]

    x_v = np.rint(points_v[:, 0] * scale).astype(np.int32)
    y_v = np.rint(points_v[:, 2] * scale).astype(np.int32)

    # for obstacle
    mask_o = (point_sum[:, 1] <= 1.0) & (point_sum[:, 1] >0.8)
    points_o = point_sum[mask_o]

    x_o = np.rint(points_o[:, 0] * scale).astype(np.int32)
    y_o = np.rint(points_o[:, 2] * scale).astype(np.int32)

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
        if points_v[i, 1] > z_buffer[y_v[i], x_v[i]]:
            z_buffer[y_v[i], x_v[i]] = points_v[i, 1]
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
    
        
    return x_min, y_min, obstacle_map


def set_enabled(widget, enable):
    widget.enabled = enable
    for child in widget.get_children():
        child.enabled = enable

class ReconstructionWindow:

    def __init__(self, font_id, send_queue= Queue(), receive_queue= Queue()):

        self.device = "cuda:0"

        self.window = gui.Application.instance.create_window(
            'Open3D - Reconstruction', 1280, 800)

        w = self.window
        em = w.theme.font_size

        spacing = int(np.round(0.25 * em))
        vspacing = int(np.round(0.5 * em))

        margins = gui.Margins(vspacing)

        # First panel
        self.panel = gui.Vert(spacing, margins)

        ## Items in adjustable props
        self.adjustable_prop_grid = gui.VGrid(2, spacing,
                                              gui.Margins(em, 0, em, 0))

        ### Update surface?
        rgb_pc_label = gui.Label('RGB PC?')
        self.rgb_pc_box = gui.Checkbox('')
        self.rgb_pc_box.checked = True
        self.adjustable_prop_grid.add_child(rgb_pc_label)
        self.adjustable_prop_grid.add_child(self.rgb_pc_box)

        ### Show trajectory?
        trajectory_label = gui.Label('Trajectory?')
        self.trajectory_box = gui.Checkbox('')
        self.trajectory_box.checked = True
        self.adjustable_prop_grid.add_child(trajectory_label)
        self.adjustable_prop_grid.add_child(self.trajectory_box)

        ## Application control
        b = gui.ToggleSwitch('Resume/Pause')
        b.set_on_clicked(self._on_switch)

        self.text_edit = gui.TextEdit()
        self.submit_button = gui.Button("Submit")
        self.submit_button.set_on_clicked(self._on_submit)
        self.input_text = None

        ## Tabs
        tab_margins = gui.Margins(0, int(np.round(0.5 * em)), 0, 0)
        tabs = gui.TabControl()


        ### Rendered image tab
        tab2 = gui.Vert(0, tab_margins)
        self.semantic_image = gui.ImageWidget()
        self.map_image = gui.ImageWidget()
        tab2.add_child(self.semantic_image)
        tab2.add_fixed(vspacing)
        tab2.add_child(self.map_image)
        tabs.add_tab('Semantic images', tab2)

        ### Input image tab
        tab1 = gui.Vert(0, tab_margins)
        self.input_color_image = gui.ImageWidget()
        self.input_depth_image = gui.ImageWidget()
        tab1.add_child(self.input_color_image)
        tab1.add_fixed(vspacing)
        tab1.add_child(self.input_depth_image)
        tabs.add_tab('Input images', tab1)

        ### Info tab
        tab3 = gui.Vert(0, tab_margins)
        self.output_info = gui.Label('Output info')
        self.output_info.font_id = font_id
        tab3.add_child(self.output_info)
        tabs.add_tab('Info', tab3)

        self.panel.add_child(gui.Label('Reconstruction settings'))
        self.panel.add_child(self.adjustable_prop_grid)
        self.panel.add_child(self.text_edit)
        self.panel.add_child(self.submit_button)
        self.panel.add_child(b)
        self.panel.add_stretch()
        self.panel.add_child(tabs)


        # Scene widget
        self.widget3d = gui.SceneWidget()

        # FPS panel
        self.fps_panel = gui.Vert(spacing, margins)
        self.output_fps = gui.Label('FPS: 0.0')
        self.fps_panel.add_child(self.output_fps)

        # Now add all the complex panels
        w.add_child(self.panel)
        w.add_child(self.widget3d)
        w.add_child(self.fps_panel)

        self.widget3d.scene = rendering.Open3DScene(self.window.renderer)
        self.widget3d.scene.set_background([1, 1, 1, 1])

        w.set_on_layout(self._on_layout)
        w.set_on_close(self._on_close)

        self.saved_objects = None
        self.saved_full_points = None
        self.saved_full_colors = None

        self.is_done = False

        self.is_started = False
        self.is_running = True

        self.idx = 0
        self.traj = []

        self.send_queue = send_queue
        self.receive_queue = receive_queue
        threading.Thread(name='UpdateMain', target=self.update_main).start()

    def _on_submit(self):
        input_text = self.text_edit.text_value
        print("Input text:", input_text)
        self.send_queue.put([input_text, self.is_running])

    def _on_layout(self, ctx):
        em = ctx.theme.font_size

        panel_width = 20 * em
        rect = self.window.content_rect

        self.panel.frame = gui.Rect(rect.x, rect.y, panel_width, rect.height)

        x = self.panel.frame.get_right()
        self.widget3d.frame = gui.Rect(x, rect.y,
                                       rect.get_right() - x, rect.height)

        fps_panel_width = 7 * em
        fps_panel_height = 2 * em
        self.fps_panel.frame = gui.Rect(rect.get_right() - fps_panel_width,
                                        rect.y, fps_panel_width,
                                        fps_panel_height)

    # Toggle callback: application's main controller
    def _on_switch(self, is_on):
        
        self.is_running = not self.is_running
        self.send_queue.put([None, self.is_running])


    def _on_close(self):
        

        return True
    
    def poses2lineset(self, poses, color=[0, 0, 1]):
        '''
        Create a open3d line set from a batch of poses

        poses: (N, 4, 4)
        color: (3,)
        '''
        N = poses.shape[0]
        lineset = o3d.geometry.LineSet()
        if np.all(np.ptp(poses, axis=0) == 0):
            return lineset
        
        lineset.points = o3d.utility.Vector3dVector(poses)
        lineset.lines = o3d.utility.Vector2iVector(
            np.array([[i, i + 1] for i in range(len(poses) - 1) 
                    if np.linalg.norm(np.array(poses[i+1]) - np.array(poses[i])) < 0.5])
        )
        lineset.colors = o3d.utility.Vector3dVector([color for _ in range(len(lineset.lines))])
        return lineset

    def init_render(self):
       
        self.window.set_needs_layout()

        bbox = o3d.geometry.AxisAlignedBoundingBox([-5, -5, -5], [5, 5, 5])
        self.widget3d.setup_camera(90, bbox, [0, 0, 0])
        # self.widget3d.setup_camera(90, bbox, [camera_matrix[3,0], camera_matrix[3,1], camera_matrix[3,2]])[0, 0, 0]
        # self.widget3d.look_at(camera_matrix[:3,0], camera_matrix[:3,1], camera_matrix[:3,2])
        self.widget3d.look_at([0, 0, 0], [-3, 4, 0], [0, 1, 0])

        # points = np.random.rand(100, 3)
        # colors = np.zeros((100, 3))
        # colors[:, 0] = 1  # 红色
        # pcd_t = o3d.t.geometry.PointCloud(
        #             o3c.Tensor(points.astype(np.float32)))
        # pcd_t.point.colors = o3c.Tensor(colors)
        # material = rendering.MaterialRecord()
        # material.shader = "defaultUnlit"
        # self.widget3d.scene.add_geometry('points', pcd_t, material)  # Add material argument

        # Add a coordinate frame
        self.widget3d.scene.show_axes(True)

    def update_render(self, 
                      point_sum_points,
                      point_sum_colors,
                      plan_paths):
        
        self.window.set_needs_layout()
        bbox = o3d.geometry.AxisAlignedBoundingBox([-5, -5, -5], [5, 5, 5])
        self.widget3d.setup_camera(90, bbox, [0, 0, 0])
        self.widget3d.look_at([0, 0, 0], [-3, 3, 0], [0, 1, 0])

        self.widget3d.scene.show_axes(True)


        self.widget3d.scene.remove_geometry("full_pcd")
        if self.rgb_pc_box.checked:
            full_pcd = o3d.t.geometry.PointCloud(
            o3c.Tensor(point_sum_points.astype(np.float32)))
            full_pcd.point.colors = o3c.Tensor(point_sum_colors.astype(np.float32))
            
            material = rendering.MaterialRecord()
            material.shader = "defaultUnlit"
            self.widget3d.scene.add_geometry('full_pcd', full_pcd, material)  # Add material argument
            

        
        # # self.widget3d.scene.remove_geometry("path_points")
        if len(plan_paths) > 0:
            for i, path in enumerate(plan_paths):
                path_lineset = self.poses2lineset(np.stack(path), color=[1.-i, i, 0])
                if path_lineset.has_lines() and path_lineset.has_points():
                    material = rendering.MaterialRecord()
                    material.shader = "unlitLine"
                    material.line_width = 10.0
                    self.widget3d.scene.add_geometry(f'path_points_{i}', path_lineset, material)



    # Major loop
    def update_main(self):
        
        gui.Application.instance.post_to_main_thread(
            self.window, lambda: self.init_render())
        
        file_path = 'data/large_scan.xyz'  
        data = np.loadtxt(file_path, delimiter=',')
        point_sum_points = data[:, :3] 
        point_sum_colors = data[:, 3:6] /255 
        
        
        scene_names = ["hallway_1", "hallway_2", "hallway_3", "hallway_4", "hallway_5", "office_1", "office_2", "office_3", "conferenceRoom_1"]
        pos = [(1000, 500), (800, 1000), (300, 2000), (900, 2900), (1200, 2000), (1300, 600), (1400, 1250), (1500, 2300), (1000, 1800)]
        all_centers = {}
        for i in range(len(scene_names)):
            all_centers[scene_names[i]] = (pos[i][1], pos[i][0])
        
        G = nx.Graph()
        
        G = nx.Graph()
        for name in scene_names:
                G.add_node(name)
                
        G.add_edge("office_1", "hallway_1")
        G.add_edge("office_2", "hallway_5")
        G.add_edge("office_3", "hallway_5")
        G.add_edge("conferenceRoom_1", "hallway_5")
        G.add_edge("hallway_4", "hallway_5")
        G.add_edge("hallway_4", "hallway_3")
        G.add_edge("hallway_2", "hallway_3")
        G.add_edge("hallway_2", "hallway_1")
        G.add_edge("hallway_5", "hallway_1")

        
        source_node = "office_1"
        target_node = "office_3"
        
        x_min, y_min, obstacle_map = get_top_view_map(point_sum_points, point_sum_colors, scene_names)

        plan_path = []
        all_topo_paths = path_finding.get_all_simple_paths(G, source_node, target_node)
        all_geo_paths = path_finding.path_plan_from_topo_graph(all_topo_paths, obstacle_map, all_centers)
        
        for i, geo_path in enumerate(all_geo_paths):
            geo_path = np.array(geo_path) 
            original_y_indices = (geo_path[:, 1] + x_min)* 0.01 
            original_x_indices = (geo_path[:, 0] + y_min)* 0.01   # Assuming you need to subtract y_max; adjust if it's a different operation
            original_z_indices = geo_path[:, 0] * 0 + 0.5
            # Re-zip to get the original geo_path format
            original_path = np.stack((original_y_indices, original_z_indices, original_x_indices), axis=-1)
            plan_path.append(original_path)

        mask = (point_sum_points[:, 1] <= 1.5)
        
        points_filtered = point_sum_points[mask]
        colors_filtered = point_sum_colors[mask]
        
        gui.Application.instance.post_to_main_thread(
            self.window, lambda: self.update_render(
                points_filtered,
                colors_filtered,
                plan_path)
                )       
        


if __name__ == '__main__':

    app = gui.Application.instance
    app.initialize()
    mono = app.add_font(gui.FontDescription(gui.FontDescription.MONOSPACE))
    w = ReconstructionWindow(mono)
    app.run()
    
    # file_path = 'data/noXYZ_area_5a_no_xyz/area_5a/3d/pointcloud.mat'  # Update this path
    # point_sum_points, point_sum_colors = load_s3dis_point_cloud(file_path)
    
    # mask = (point_sum_points[:, 2] <= 1.5)
    
    # points_filtered = point_sum_points[mask]
    # colors_filtered = point_sum_colors[mask]
    
    # # Orthographic Projection (ignoring Z-coordinate)
    # x = points_filtered[:, 0]
    # y = points_filtered[:, 1]

    # points_2d = points_filtered[:, [0, 1]]
    # x_min, y_min = np.min(points_2d, axis=0)
    # x_max, y_max = np.max(points_2d, axis=0)

    # scale = 3000  # Size of the image in pixels
    # points_2d_normalized = (points_2d - [x_min, y_min]) / ([x_max - x_min, y_max - y_min])
    # points_2d_scaled = (points_2d_normalized * scale).astype(np.int32)
    
    # # Store the highest Z value for each pixel
    # z_buffer = np.full((scale, scale), -np.inf)
    
    # # Create an empty black image
    # image = np.zeros((scale, scale, 3), dtype=np.uint8)

    # # Convert colors from [0, 1] to [0, 255] and to BGR format for OpenCV
    # colors_scaled = (colors_filtered * 255).astype(np.uint8)
    # colors_bgr = colors_scaled[:, [2, 1, 0]]  # RGB to BGR

    # # Draw each point with color
    # for (x, y), z, color in zip(points_2d_scaled, points_filtered[:, 2], colors_bgr):
    #     if x < scale and y < scale and z > z_buffer[x, y]:
    #         z_buffer[x, y] = z
    #         cv2.circle(image, (x, y), 1, color.tolist(), -1)  # Draw the point

    #     # cv2.circle(image, (x, z), 1, color.tolist(), -1)  # Draw colored points
    

    # cv2.imshow('Top View Projection with Color', image)
    # cv2.waitKey(0) 
