import warnings
import pyart
import numpy as np
from matplotlib import pyplot as plt
import glob
from datetime import datetime
import os
import shutil
import multiprocessing as mp


def _drop_fields(radar):
    fields_to_drop = ["PURPLE_HAZE"]
    for field in fields_to_drop:
        if field in radar.fields:
            del radar.fields[field]

    return radar


def dealiase(radar, vel_name='velocity', gatefilter=None, method="unwrap"):
    if gatefilter is None:
        gatefilter = pyart.correct.GateFilter(radar)
        gatefilter.include_above("REF", 0)
        gatefilter.exclude_masked('REF')
        gatefilter.exclude_invalid('REF')
        gatefilter.exclude_transition()
    
    if method == "unwrap":
        corr_vel = pyart.correct.dealias_unwrap_phase(radar, vel_field=vel_name,
                                                      keep_original=False, gatefilter=gatefilter)
    elif method == "region":
        corr_vel = pyart.correct.dealias_region_based(radar, vel_field=vel_name,
                                                      keep_original=False, gatefilter=gatefilter)
    
    radar.add_field(vel_name, corr_vel, replace_existing=True)
    return radar


def filter_data(radar, refl_field, vel_field, dealias_method="region"):
    radar = _drop_fields(radar)
    radar.scan_type = b'ppi'
    radar = dealiase(radar, vel_name=vel_field, gatefilter=None, method=dealias_method)
    return radar


def get_nexrad_data_files(start_time: str, end_time: str) -> list:
    start_datetime = datetime.strptime(start_time, '%Y%m%d%H%M%S')
    end_datetime = datetime.strptime(end_time, '%Y%m%d%H%M%S')
    
    nexrad_dir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/NEXRAD/"
    data_files = []
    for iop in ["IOP2"]:
        for radar_name in ['KGWX']:
            data_files.extend(sorted(glob.glob(f"{nexrad_dir}{iop}/{radar_name}/*V06.nc")))
    
    data_files_filtered = []
    for file in data_files:
        file_datetime_str = file.split('/')[-1].split("KGWX")[1].split("_V")[0]
        file_datetime = datetime.strptime(file_datetime_str, '%Y%m%d_%H%M%S')
        if start_datetime <= file_datetime < end_datetime:
            data_files_filtered.append(file)
    
    print("Available files: ", len(data_files_filtered))
    return data_files_filtered


def process_file(outdir, rfile):
    try:
        print(f'Reading file: {os.path.basename(rfile)}')
        radar = pyart.io.read(rfile)
        radar = filter_data(radar, "DBZ", "VEL")
        max_rng = 200.0 * 1e3
        grid = pyart.map.grid_from_radars(radar, (41, 801, 801),
                                          ((0., 10e3), (-max_rng, max_rng), (-max_rng, max_rng)),
                                          weighting_function='Barnes2',
                                          fields=['REF', 'VEL', 'ZDR', "RHO"])

        print(f'Deleting Radar Object: {os.path.basename(rfile)}')
        del radar        
        print(f"Saving in: {grid_file_path} as {os.path.basename(rfile)}\n")
        # Write grid
        pyart.io.write_grid(filename=os.path.join(grid_file_path, os.path.basename(rfile)), grid=grid)
    except Exception as e:
        print(f"Error processing file: {os.path.basename(rfile)}")
        print(str(e))


def process_file_wrapper(args):
    return process_file(*args)


if __name__ == "__main__":
    outdir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/GRID"
    data_files = get_nexrad_data_files("20220330220000", "20220331040000")
    global grid_file_path
    grid_file_path = os.path.join(outdir, "IOP2/KGWX/")

    # Create a pool of worker processes
    pool = mp.Pool()

    # Map the data files to the process_file_wrapper function to process them in parallel
    results = pool.map(process_file_wrapper, [(outdir, f) for f in data_files])

    # Close the pool of worker processes
    pool.close()
    pool.join()