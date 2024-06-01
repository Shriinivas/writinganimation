#
# This Blender add-on creates writing animation for the selected Bezier curves
# Supported Blender Version: 2.8x and above
#
# Author: Shrinivas Kulkarni (khemadeva@gmail.com)

from .writinganim import register, unregister

bl_info = {
    "name": "Create Writing Animation",
    "author": "Shrinivas Kulkarni",
    "location": "Properties > Active Tool and Workspace Settings > Create Writing Animation",
    "category": "Animation",
    "blender": (2, 80, 0),
}

if __name__ == "__main__":
    register()
