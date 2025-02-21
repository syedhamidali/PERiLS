import warnings
warnings.filterwarnings("ignore")
import pyart
import numpy as np
from matplotlib import pyplot as plt
import glob, os, sys, re
from PIL import Image

basedir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/Illinois_Mobile_Radar/IOP1/"
radar_type = ["COW1", "DOW7", "DOW8"]
data_folder = "QCed"

cow1_files = glob.glob(f"{basedir}{radar_type[0]}{os.sep}{data_folder}{os.sep}*.nc")
savedir = f"{basedir}{'plots'}{os.sep}"

for cfile in cow1_files:
    radar = pyart.io.read_cfradial(cfile)
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=(12, 10), constrained_layout = True)
    ax = plt.subplot(221)
    display.plot_ppi('DBZH', 0, vmin=-10., vmax = 60, cmap = 'pyart_HomeyerRainbow')
    ax = plt.subplot(222)
    display.plot_ppi('VEL_F', 0, vmin=-30., vmax = 30, cmap = 'pyart_NWSVel')
    ax = plt.subplot(223)
    display.plot_ppi('ZDRC', 0, vmin = -7.9, vmax = 7.9, cmap = pyart.graph.cm.RefDiff)
    ax = plt.subplot(224)
    display.plot_ppi('PHIDP', 0, vmin = -179, vmax = 179, cmap = pyart.graph.cm.RefDiff)
    filenames = os.path.join(savedir, cfile.split(os.sep)[-1].split('_to_')[-1].split('.nc')[0] + '.png')
    plt.savefig(filenames, bbox_inches = "tight")
    plt.close()
    del radar
    del display
    
imgs = glob.glob(os.path.join(savedir, '*.png'))
# sorting the files by time
imgs.sort(key=lambda x: os.path.getmtime(x))

images = []
for file_name in imgs:
    images.append(Image.open(file_name))

images[0].save(os.path.join(savedir,'animation.gif'), save_all=True, append_images=images[1:], duration=5*1000/len(images), loop=0)