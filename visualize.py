import mat73
import matplotlib.pyplot as plt
import cv2


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

    # Iterate through the Disjoint_Space structures
    for disjoint_space in area['Disjoint_Space']:
        print(f"Processing {disjoint_space['name']}...")

        for i in range(len(disjoint_space['object']['points'])):
            obj_points = np.array(disjoint_space['object']['points'][i]) # Transpose to get Nx3 shape
            obj_colors = np.array(disjoint_space['object']['RGB_color'][i])/255  # Normalize to 0-1 range

            points.append(obj_points)
            colors.append(obj_colors)
        # break
    # Concatenate all points and colors
    all_points = np.concatenate(points, axis=0)
    all_colors = np.concatenate(colors, axis=0)
    
    return all_points, all_colors



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
    


    def init_render(self):
       
        self.window.set_needs_layout()

        bbox = o3d.geometry.AxisAlignedBoundingBox([-5, -5, -5], [5, 5, 5])
        self.widget3d.setup_camera(90, bbox, [0, 0, 0])
        # self.widget3d.setup_camera(90, bbox, [camera_matrix[3,0], camera_matrix[3,1], camera_matrix[3,2]])[0, 0, 0]
        # self.widget3d.look_at(camera_matrix[:3,0], camera_matrix[:3,1], camera_matrix[:3,2])
        self.widget3d.look_at([0, 0, 0], [-3, 4, 0], [0, 1, 0])

        points = np.random.rand(100, 3)
        colors = np.zeros((100, 3))
        colors[:, 0] = 1  # 红色
        pcd_t = o3d.t.geometry.PointCloud(
                    o3c.Tensor(points.astype(np.float32)))
        pcd_t.point.colors = o3c.Tensor(colors)
        material = rendering.MaterialRecord()
        material.shader = "defaultUnlit"
        self.widget3d.scene.add_geometry('points', pcd_t, material)  # Add material argument

        # Add a coordinate frame
        self.widget3d.scene.show_axes(True)

    def update_render(self, 
                      point_sum_points,
                      point_sum_colors,):
        
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
            

      




    # Major loop
    def update_main(self):
        
        gui.Application.instance.post_to_main_thread(
            self.window, lambda: self.init_render())
        
        # Example usage
        file_path = 'data/noXYZ_area_3_no_xyz/area_3/3d/pointcloud.mat'  # Update this path
        point_sum_points, point_sum_colors = load_s3dis_point_cloud(file_path)
        
        mask = (point_sum_points[:, 2] <= 1.5)
        
        points_filtered = point_sum_points[mask]
        colors_filtered = point_sum_colors[mask]
        
        gui.Application.instance.post_to_main_thread(
            self.window, lambda: self.update_render(
                points_filtered,
                colors_filtered)
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
