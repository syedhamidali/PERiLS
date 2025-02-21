'''
@Date: May 25, 2022
@Author: H. A. Syed
@Email: syed44@purdue.edu
@Advisor: Prof. Dan Dawson
'''

import warnings
warnings.filterwarnings("ignore")
import pyart
# import matplotlib.pyplot as plt
import numpy as np
# import xarray as xr
import nexradaws
import tempfile
import os
import shutil
from datetime import datetime, timedelta
tstart = datetime.now()
# import cartopy.crs as ccrs
# import cartopy.feature as cfeature
# import metpy.calc as mpcalc
# import metpy.plots as mpplots
# from matplotlib.patheffects import withStroke
# from metpy.io import parse_metar_file
# from metpy.units import pandas_dataframe_to_unit_arrays
# Here is where we import the TDSCatalog class from siphon for obtaining our data 
from siphon.catalog import TDSCatalog
import pytz
import pathlib

#  which radar(s)?
radar_name = ["KBMX", "KGWX", "KPOE", "KHTX", "KDGX", "KLCH", "KLZK", "KNQA", "KPAH", "KSHV"]
for name in radar_name:

    # Define data directory
    data_dir = "/Users/syed44/Downloads/Project/PERiLS/obsdata/2022/NEXRAD/IOP4/"+name
    pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)

    # Create a tempory file, connect nexrad aws and request a list of files for the Perils campaign
    templocation = tempfile.mkdtemp()
    conn = nexradaws.NexradAwsInterface()

    # Define the date
    scans = conn.get_avail_scans(2022, 4, 13, name)
    print(len(scans))

    lcn = templocation
    localfiles = conn.download(scans,lcn)

    fpath = []
    for file in range(0,len(scans)):
        if localfiles.success[file].filepath.endswith("MDM"):
            continue
        fpath.append(localfiles.success[file].filepath)
        # print(localfiles.success[file].filepath)
    print("Total no. of files to be saved: ", len(fpath))

    print("Saving Cf-radial data")
    for file in fpath:
        radar = pyart.io.read(file)
        pyart.io.write_cfradial(data_dir+"/"+file.split("/")[-1]+'.nc',radar)
        print("Successfully converted: ", file.split("/")[-1])
print("All done")
print("Total time taken to complete: ",datetime.now()-tstart)