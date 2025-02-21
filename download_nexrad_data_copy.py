'''
@Date: Oct 7, 2022
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
from siphon.catalog import TDSCatalog
import pytz
import pathlib

#  which radar(s)?
radar_name = ["KMXX"] #["KBMX", "KGWX", "KPOE", "KHTX", "KDGX", "KLCH", "KLZK", "KNQA", "KPAH", "KSHV"]
for name in radar_name:

    # Define data directory
    data_dir = "/Users/syed44/Downloads/Project/PERiLS/obsdata/2022/NEXRAD/IOP3/"+name
    pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)

    # Create a tempory file, connect nexrad aws and request a list of files for the Perils campaign
    # templocation = tempfile.mkdtemp()
    conn = nexradaws.NexradAwsInterface()

    # Define the date
    scans = conn.get_avail_scans(2022, 4, 5, name)
    print(len(scans))

    # lcn = templocation
    localfiles = conn.download(scans,data_dir)

    # fpath = []
    # for file in range(0,len(scans)):
    #     if localfiles.success[file].filepath.endswith("MDM"):
    #         continue
    #     fpath.append(localfiles.success[file].filepath)
    #     # print(localfiles.success[file].filepath)
    # print("Total no. of files to be saved: ", len(fpath))

    # print("Saving Cf-radial data")
    # for file in fpath:
    #     radar = pyart.io.read(file)
    #     pyart.io.write_cfradial(data_dir+"/"+file.split("/")[-1]+'.nc',radar)
    #     print("Successfully converted: ", file.split("/")[-1])
print("All done")
print("Total time taken to complete: ",datetime.now()-tstart)

## 1.  Go to the data_dir via terminal and remove the files that ends with _MDM
##      rm -rf *_MDM
##
## 2. convert to cfradial by using lrose
##      RadxConvert -f KMXX* -outdir . 
## The period/dot means the current directory from where you are issuing the command
##
## 3. Renaming the files according to the NEXRAD naming convention
##      (see renaming_cfrad.ipynb)

