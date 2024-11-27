import omni.ext
import omni.ui as ui
from omni.kit.window.filepicker import FilePickerDialog
import omni.usd
from pxr import Gf, UsdGeom, Sdf
import os
import pandas as pd
import numpy as np

class CompanyHelloWorldExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[company.hello.world] company hello world startup")
        self._stage = omni.usd.get_context().get_stage()
        self._points_path = "/World/Points"
        
        self._window = ui.Window("Point Cloud Visualizer", width=300, height=200)
        with self._window.frame:
            with ui.VStack(spacing=5):
                ui.Label("Select a CSV file with x,y,z,bm columns", height=20)
                self._file_path_label = ui.Label("No file selected", height=20)
                self._analysis_label = ui.Label("", height=60)
                
                def on_click_select():
                    dialog = FilePickerDialog(
                        'Select CSV File',
                        allow_multi_selection=False,
                        apply_button_label="Select",
                        click_apply_handler=lambda filename, dirname: on_click_apply(filename, dirname),
                        click_cancel_handler=lambda filename, dirname: on_click_cancel(filename, dirname),
                        file_extension_options=[("CSV Files", "*.csv")]
                    )
                    
                    def on_click_apply(filename: str, dirname: str):
                        if filename and dirname:
                            full_path = os.path.join(dirname, filename)
                            self._file_path_label.text = full_path
                            self.process_csv_file(full_path)
                    
                    def on_click_cancel(filename: str, dirname: str):
                        print("File selection cancelled")
                    
                    dialog.show()
                
                # Just two simple buttons
                with ui.HStack(height=30):
                    ui.Button("Select CSV", clicked_fn=on_click_select)
                    ui.Button("Clear Points", clicked_fn=self.clear_points)

    def process_csv_file(self, file_path):
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            print(f"Read CSV file with {len(df)} rows")
            
            # Filter points where bm == 1
            points_df = df[df['bm'] == 1][['x', 'y', 'z']]
            print(f"Found {len(points_df)} points with bm=1")
            
            # Rotate the points before creating cubes
            points = points_df.astype(float).values
            # Swap y and z coordinates and negate z to put bottom face down
            points = points[:, [0, 2, 1]]  # Swap y and z
            points[:, 2] = -points[:, 2]   # Negate new z (old y)
            
            # Create points in the stage with rotated coordinates
            self.create_point_cubes(pd.DataFrame(points, columns=['x', 'y', 'z']))
            
            self._analysis_label.text = f"Created {len(points_df)} points"
            
        except Exception as e:
            self._analysis_label.text = f"Error processing CSV: {str(e)}"
            print(f"Error processing CSV file: {e}")
            import traceback
            traceback.print_exc()

    def create_point_cubes(self, points_df):
        """Create cubes for each point in the dataframe"""
        # Clear existing points
        self.clear_points()
        
        # Get the stage
        stage = self._stage
        
        # Create a new Xform for our points
        points_xform = UsdGeom.Xform.Define(stage, self._points_path)
        
        # Convert points to float arrays and scale them
        points = points_df.astype(float).values
        scale = 100  # Scale factor
        points = points * scale
        
        # Create a cube for each point
        for i, point in enumerate(points):
            x, y, z = point
            
            # Create a cube at this point
            cube_path = f"{self._points_path}/cube_{i}"
            cube = UsdGeom.Cube.Define(stage, cube_path)
            
            # Set cube size
            cube.CreateSizeAttr().Set(100.0)  # Fixed size that worked well before
            
            # Set position
            xform = UsdGeom.Xformable(cube.GetPrim())
            translate_op = xform.AddTranslateOp()
            translate_op.Set(Gf.Vec3d(x, y, z))
            
            # Set color (bright red for visibility)
            cube.CreateDisplayColorAttr().Set([(1.0, 0.0, 0.0)])

    def clear_points(self):
        """Remove all points from the stage"""
        if self._stage.GetPrimAtPath(self._points_path):
            self._stage.RemovePrim(self._points_path)

    def on_shutdown(self):
        print("[company.hello.world] company hello world shutdown")
        self.clear_points()