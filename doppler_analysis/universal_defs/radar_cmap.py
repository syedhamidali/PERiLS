from matplotlib import colors
import numpy as np
def radar_cmap():
    hrrr_reflectivity_colors = [
    "#00ecec", # 5
    "#01a0f6", # 10
    "#0000f6", # 15
    "#00ff00", # 20
    "#00c800", # 25
    "#009000", # 30
    "#ffff00", # 35
    "#e7c000", # 40
    "#ff9000", # 45
    "#ff0000", # 50
    "#d60000", # 55
    "#c00000", # 60
    "#ff00ff", # 65
    "#9955c9", # 70
    "#808080"  # 75
    ]
    cmap = colors.ListedColormap(hrrr_reflectivity_colors)
    return cmap

refl_range = range(5,76,5) # defines our contour intervals
rcmap = radar_cmap() # defines the color map that will accompany our filled contours and colorbar