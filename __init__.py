#
# This Blender add-on creates writing animation for the selected Bezier curves
# Supported Blender Version: 2.8x
#
# Copyright (C) 2018  Shrinivas Kulkarni
#
# License: GPL (https://github.com/Shriinivas/writinganimation/blob/master/LICENSE)
#

from . writinganim_2_8 import register, unregister

bl_info = {
    "name": "Create Writing Animation",
    "author": "Shrinivas Kulkarni",
    "location": "Properties > Active Tool and Workspace Settings > Create Writing Animation",
    "category": "Animation",
    "blender": (2, 80, 0),    
}

if __name__ == "__main__":
    register()

