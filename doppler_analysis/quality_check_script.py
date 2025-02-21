import warnings
warnings.filterwarnings("ignore")
import pyart
import datetime as dt
import numpy as np
import glob, os, sys, re
import pathlib
from collections import Counter

tstart = dt.datetime.now()

def align_radar_coords(radar):
    lons, lon_counts = np.unique(radar.longitude['data'], return_counts = True)
    c_lon = lons[np.argmax(lon_counts)]
    radar.longitude['data'] = np.array([c_lon])
    lats, lat_counts = np.unique(radar.latitude['data'], return_counts = True)
    c_lat = lats[np.argmax(lat_counts)]
    radar.latitude['data'] = np.array([c_lat])
    alts, alt_counts = np.unique(radar.altitude['data'], return_counts = True)
    c_alt = alts[np.argmax(alt_counts)]
    radar.altitude['data'] = np.array([c_alt])
    alts_agl, alt_agl_counts = np.unique(radar.altitude_agl['data'], return_counts = True)
    c_alt_agl = alts_agl[np.argmax(alt_agl_counts)]
    radar.altitude_agl['data'] = np.array([c_alt_agl])
    return radar

def filter_radar(radar, vel_field="VEL_F", refl_field="DBZHCC_F", 
                 ncp_field="NCP", rhv_field="RHOHV", phi_field="PHIDP"):
    '''Remove noise based on velocity texture and mask all the fields'''
    # Drop some fields
    fields_to_drop = ["DBMHC", "DBMVC", "VEL", "VS", "VS_F", "VL", "VL_F", "DBZHCC"]
    for field in fields_to_drop:
        if field in radar.fields:
            del radar.fields[field]
        
    texture = pyart.retrieve.calculate_velocity_texture(radar, 
                                                        vel_field=vel_field, 
                                                        wind_size=7, 
                                                        check_nyq_uniform=False)
    radar.add_field('VT',texture,replace_existing=True)
    # create gatefilter
    gf = pyart.filters.GateFilter(radar)
    gf.exclude_invalid(refl_field)
    gf.exclude_outside(refl_field, -20, 90)
    gf.exclude_below("SNRHC", 10)
    gf.exclude_above('VT', 10) # Value found by trial and error for this case
    gf_despeckeld = pyart.correct.despeckle_field(radar, refl_field, gatefilter=gf)
    corr_ZH = radar.fields[refl_field].copy()
    ZH_array = np.ma.masked_where(gf_despeckeld.gate_included == False, radar.fields[refl_field]['data'])
    corr_ZH['data'] = ZH_array
    radar.add_field('DBZH',corr_ZH,replace_existing=True)
    
    # get the mask
    mask = np.ma.getmask(radar.fields['DBZH']['data'])
    
    # iterate through remaining fields
    for field in radar.fields.keys():
        # mask the field
        radar.fields[field]['data'] = np.ma.masked_where(mask, radar.fields[field]['data'])
    return radar

def dealiase(radar, vel_name):
    #check to see if radar object has nyquist velocity
    try: 
        gatefilter = pyart.correct.GateFilter(radar)
        corr_vel   = pyart.correct.dealias_region_based(
            radar, vel_field=vel_name, keep_original=False, gatefilter = gatefilter)
        radar.add_field(vel_name, corr_vel, True)
    except:
        None

def natural_sort_key(s, _re=re.compile(r'(\d+)')):
    return [int(t) if i & 1 else t.lower() for i, t in enumerate(_re.split(s))]


basedir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/Illinois_Mobile_Radar/"
iop1 = os.path.join(basedir,"IOP1")

cow1 = os.path.join(iop1, "COW1/merged/")
dow7 = os.path.join(iop1, "DOW7/merged/")
dow8 = os.path.join(iop1, "DOW8/merged/")

cow1_files = sorted(glob.glob(os.path.join(cow1,"*nc")), key=natural_sort_key)
print(f'No. of COW1 files: {len(cow1_files)}')
dow7_files = sorted(glob.glob(os.path.join(dow7,"*nc")), key=natural_sort_key)
print(f'No. of DOW7 files: {len(dow7_files)}')
dow8_files = sorted(glob.glob(os.path.join(dow8,"*nc")), key=natural_sort_key)
print(f'No. of DOW8 files: {len(dow8_files)}')

out_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/Illinois_Mobile_Radar/IOP1/"
radar_type = ["COW1", "DOW7", "DOW8"]

for file in cow1_files:
    radar = pyart.io.read(file)
    radar = filter_radar(radar)
    dealiase(radar, 'VEL_F')
    radar = align_radar_coords(radar)
    pathlib.Path(f"{out_dir}{os.sep}{radar_type[0]}{os.sep}QCed{os.sep}").mkdir(parents=True, exist_ok=True)
    pyart.io.write_cfradial(filename=f"{out_dir}{os.sep}{radar_type[0]}{os.sep}QCed{os.sep}{file.split(os.sep)[-1]}", radar=radar,)
    print(file.split(os.sep)[-1])
#     print(f"{out_dir}{os.sep}{radar_type[0]}{os.sep}QCed{os.sep}{file.split(os.sep)[-1]}")
    
for file in dow7_files:
    radar = pyart.io.read(file)
    radar = filter_radar(radar)
    dealiase(radar, 'VEL_F')
    radar = align_radar_coords(radar)
    pathlib.Path(f"{out_dir}{os.sep}{radar_type[1]}{os.sep}QCed{os.sep}").mkdir(parents=True, exist_ok=True)
    pyart.io.write_cfradial(filename=f"{out_dir}{os.sep}{radar_type[1]}{os.sep}QCed{os.sep}{file.split(os.sep)[-1]}", radar=radar,)
    print(file.split(os.sep)[-1])
#     print(f"{out_dir}{os.sep}{radar_type[1]}{os.sep}QCed{os.sep}{file.split(os.sep)[-1]}")
    
for file in dow8_files:
    radar = pyart.io.read(file)
    radar = filter_radar(radar)
    dealiase(radar, 'VEL_F')
    radar = align_radar_coords(radar)
    pathlib.Path(f"{out_dir}{os.sep}{radar_type[2]}{os.sep}QCed{os.sep}").mkdir(parents=True, exist_ok=True)
    pyart.io.write_cfradial(filename=f"{out_dir}{os.sep}{radar_type[2]}{os.sep}QCed{os.sep}{file.split(os.sep)[-1]}", radar=radar,)
    print(file.split(os.sep)[-1])
#     print(f"{out_dir}{os.sep}{radar_type[2]}{os.sep}QCed{os.sep}{file.split(os.sep)[-1]}")

print(dt.datetime.now()-tstart)
