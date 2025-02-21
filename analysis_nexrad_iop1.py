import warnings
warnings.filterwarnings("ignore")
import pyart
import numpy as np
# import xarray as xr
# from datetime import datetime, timedelta
import matplotlib.pyplot as plt
# import cartopy.crs as ccrs
# import cartopy.feature as feat
import glob
import os
import pathlib
# import wradlib as wrl
import warnings
warnings.filterwarnings("ignore")

# zdr_lev = np.linspace(-7.9, 7.9)
# rhohv_lev = np.linspace(0,1)
# vel_lev = range(-30,30)
# ref_lev = range(-10,60)
# xlim = (-3e5, 3e5)

iop = ["IOP1",]# "IOP2", "IOP3", "IOP4"]
radar_names = ['KDGX', 'KLCH', 'KPAH', 'KGWX', 'KPOE', 'KNQA', 'KHTX', 'KLZK', 'KSHV', 'KBMX']

for iop_name in iop:
    for radar_name in radar_names:
        data_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/NEXRAD/"+iop_name+"/"+radar_name
        plots_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/NEXRAD/plots/"+iop_name+"/"+radar_name
        pathlib.Path(plots_dir).mkdir(parents=True, exist_ok=True)
#         print("data_dir",data_dir)
#         print("plots_dir",plots_dir)
        files = sorted(glob.glob(data_dir+"/"+"*nc"))
#         print(iop_name,radar_name,len(files))
        for file in files:
#             print(file)
            print("Reading", file.split('/')[-1])
            radar = pyart.io.read(file)
            display = pyart.graph.RadarDisplay(radar)
            fig = plt.figure(figsize=[18,16])
            ax1 = plt.subplot(221)
            display.plot_ppi("reflectivity",1,vmin=-10,vmax=60, cmap="pyart_NWSRef", ax=ax1)
            ax2 = plt.subplot(222)
            display.plot("differential_reflectivity",1,vmin=-7.9,vmax=7.9, cmap="pyart_RefDiff", 
                                 ax=ax2)
            ax3 = plt.subplot(223)
            display.plot("velocity",1,vmin=-30,vmax=30, cmap="pyart_NWSVel",ax=ax3)

            ax4 = plt.subplot(224)
            display.plot("cross_correlation_ratio",1,vmin=0,vmax=1, cmap="pyart_NWS_SPW",ax=ax4)
            for ax in [ax1,ax2,ax3,ax4]:
                ax.set_xlim(-300, 300)
                ax.set_ylim(-300, 300)
            plt.savefig(plots_dir+"/"+file.split("/")[-1].split(".")[0]+".png",dpi=100)
            print("saved", file.split('/')[-1])
            plt.close()
            del radar
        plots_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/NEXRAD/plots/"+iop_name+"/"+radar_name
#         print(plots_dir)
        fp_in = plots_dir+"/"+"*.png"
        fp_out  = "/home/syed44/Projects/PERiLS/plots/"+iop_name+"_"+radar_name+".gif"
#         print("IN",fp_in)
#         print("OUT",fp_out)
        img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
        img.save(fp=fp_out, format='GIF', append_images=imgs,
                 save_all=True, duration=300, loop=0)
     