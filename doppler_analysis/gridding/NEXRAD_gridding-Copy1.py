import warnings
warnings.filterwarnings("ignore")
import pyart
import numpy as np
from pyart.retrieve import get_freq_band
from matplotlib import pyplot as plt
import glob, os
from datetime import datetime
import time
import sys
sys.path.append("../")
import nearest_nexrad as nrnx


print(nrnx.nearest_sites(33.75801, -88.44617, 1))

nexrad_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/NEXRAD/"


def _drop_fields(radar):
    fields_to_drop = ["PURPLE_HAZE"]
    for field in fields_to_drop:
        if field in radar.fields:
            del radar.fields[field]

    return radar


#function to dealiase the Doppler velocity
def dealiase(radar, vel_name='velocity', gatefilter=None, method="unwrap"):
    '''
    Dealias Doppler velocities using Py-ART.
    method : str
        Method to use for the dealiasing. Can be 'unwrap' or 'region'.
    '''
    # Create a GateFilter if one was not provided
    if gatefilter is None:
        gatefilter = pyart.correct.GateFilter(radar)
        gatefilter.include_above("REF", 0)
        gatefilter.exclude_masked('REF')
        gatefilter.exclude_invalid('REF')
        gatefilter.exclude_transition()
    # Dealias Doppler velocities using the selected method
    if method == "unwrap":
        corr_vel = pyart.correct.dealias_unwrap_phase(radar, vel_field=vel_name,
                                                      keep_original=False, gatefilter=gatefilter)
    elif method == "region":
        corr_vel = pyart.correct.dealias_region_based(radar, vel_field=vel_name,
                                                      keep_original=False, gatefilter=gatefilter)
    # Add the dealiased Doppler velocities to the radar object
    radar.add_field(vel_name, corr_vel, replace_existing=True)
    return radar


def filter_data(radar, refl_field, vel_field, dealias_method="region"):
    '''Remove noise based on velocity texture,snr, and rhohv, and mask all the fields'''
    # Drop some fields
    radar = _drop_fields(radar)
    # Align radar coords
    radar.scan_type = b'ppi'
    # Dealias
    radar = dealiase(radar, vel_name=vel_field, gatefilter=None, method=dealias_method)
    return radar


def get_nexrad_data_files(start_time: str, end_time: str) -> list:
    '''start_time: str ('YYYYMMDDHHMMSS')
       end_time: str ('YYYYMMDDHHMMSS')'''
    
    start_datetime = datetime.strptime(start_time, '%Y%m%d%H%M%S')
    end_datetime = datetime.strptime(end_time, '%Y%m%d%H%M%S')
    
    nexrad_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/NEXRAD/"
    radar_site = ['KGWX']
    data_files = []
    for iop in ["IOP2"]:
        for radar_name in radar_site:
            data_files.extend(sorted(glob.glob(f"{nexrad_dir}{iop}/{radar_name}/*V06.nc")))
    
    data_files_filtered = []
    for file in data_files:
#         print(file.split('/')[-1].split("KGWX")[1].split("_V")[0])
        file_datetime_str = file.split('/')[-1].split("KGWX")[1].split("_V")[0]
        file_datetime = datetime.strptime(file_datetime_str, '%Y%m%d_%H%M%S')
        if start_datetime <= file_datetime < end_datetime:
            data_files_filtered.append(file)
    
    print("Available files: ", len(data_files_filtered))
#     for file in data_files_filtered:
#         print(file.split("/")[-1])
        
    return data_files_filtered


# Define a function that takes a file name and writes the GRID file
def process_file(nexrad_dir, rfile):
    print(f'Reading file: {rfile.split("/")[-1]}')
    radar = pyart.io.read(rfile)
    radar = filter_data(radar, "DBZ", "VEL")
#     max_rng = np.ceil(radar.range['data'].max())
    grid = pyart.map.grid_from_radars(radar,(60,700,700),
                                      ((0.,15000.),(-350*1e3, 350*1e3),(-350*1e3, 350*1e3)), 
                                      weighting_function='Barnes2',
                                      fields=['REF', 'VEL', 'ZDR']
                                     )
    
    print(f'Deleting: {rfile.split("/")[-1]}')
    del radar

    # Extract the NEXRAD file number from the file name
    file_number = rfile.split('NEXRAD')[-1]

    # Construct the full path to the GRID file using os.path.join()
    grid_file_path = os.path.join(nexrad_dir, f'GRID2{file_number}')
    
    print(f'Saving Grid: {rfile.split("/")[-1]}')
    # Write the GRID file using pyart.io.write_grid()
    pyart.io.write_grid(filename=grid_file_path, grid=grid)


nexrad_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/NEXRAD/"
data_files = get_nexrad_data_files("20220330220000", "20220331040000")


# Loop over data_files and call process_file() for each file
for rfile in data_files:
    process_file(nexrad_dir, rfile)