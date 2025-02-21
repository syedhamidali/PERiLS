'''
import urllib.request
url = "https://raw.githubusercontent.com/syedhamidali/test_scripts/master/map_features.py"
urllib.request.urlretrieve(url, "map_features.py")
import map_features as mf
'''


import cartopy.crs as ccrs
import cartopy.feature as feat
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from metpy.plots import USCOUNTIES

def map_features(ax, b=False, l=False, t=False, r=False, coastline=False, 
                     borders=False, ocean=False, states=True, counties=False, 
                     land=False, grids=False):
    '''Add cartopy features to the axis'''
    gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=0.3, color='black', 
                      alpha=0.3, linestyle='-', draw_labels=True)
    gl.xlabels_top = t
    gl.xlabels_bottom = b
    gl.ylabels_left = l
    gl.ylabels_right = r
    if grids:
        gl.xlines = True
        gl.ylines = True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    if borders:
        ax.add_feature(feat.BORDERS, lw = 0.5)
    if land:
        ax.add_feature(feat.LAND, lw = 0.3, fc = [0.9,0.9,0.9])
    if coastline:
        ax.add_feature(feat.COASTLINE, lw = 0.5)
    if ocean:
        ax.add_feature(feat.OCEAN, alpha = 0.5)
    if states:
        ax.add_feature(feat.STATES.with_scale("10m"), alpha = 0.5, lw = 0.5)
    if counties:
        ax.add_feature(USCOUNTIES.with_scale('500k'), alpha=0.3, linestyle=':', lw = 0.3)