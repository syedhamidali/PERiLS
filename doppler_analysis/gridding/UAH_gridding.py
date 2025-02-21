import multiprocessing as mp
import time
import os
import glob
# from matplotlib import pyplot as plt
from pyart.retrieve import get_freq_band
import numpy as np
import pyart
import warnings
warnings.filterwarnings("ignore")
# from pymeso import llsd
# import scipy


def _drop_fields(radar):
    fields_to_drop = ["total_power", "spectrum_width", "differential_reflectivity",
                      'specific_differential_phase', 'differential_phase', 'normalized_coherent_power']
    for field in fields_to_drop:
        if field in radar.fields:
            del radar.fields[field]
    return radar


# function to dealiase the Doppler velocity
def dealiase(radar, vel_name='VEL', gatefilter=None, method="unwrap"):
    '''
    Dealias Doppler velocities using Py-ART.
    method : str
        Method to use for the dealiasing. Can be 'unwrap' or 'region'.
    Returns
    -------
    radar
    '''
    # Create a GateFilter if one was not provided
    if gatefilter is None:
        gatefilter = pyart.correct.GateFilter(radar)
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


def _rename_moms(radar):
    '''Rename fields'''
    radar.fields['REF'] = radar.fields.pop('reflectivity')
    radar.fields['VEL'] = radar.fields.pop('velocity')
    radar.fields['ZDR'] = radar.fields.pop('c_zdr')
    radar.fields['RHO'] = radar.fields.pop('cross_correlation_ratio')

    return radar


def process_file(outdir, rfile):
    try:
        print(f'Reading file: {os.path.basename(rfile)}')
        radar = pyart.io.read(rfile)
        radar = _drop_fields(radar)
        radar = _rename_moms(radar)
        radar = dealiase(radar, vel_name="VEL", method='region')
        max_rng = 99750.0
        grid = pyart.map.grid_from_radars(radar, (41, 400, 400),
                                          ((0., 10e3), (-max_rng, max_rng),
                                           (-max_rng, max_rng)),
                                          weighting_function='Barnes2',
                                          fields=['REF', 'VEL', 'ZDR', "RHO"])

        print(f'Deleting Radar Object: {os.path.basename(rfile)}')
        del radar
        print(f"Saving in: {grid_file_path} as {os.path.basename(rfile)}\n")
        # Write grid
        pyart.io.write_grid(filename=os.path.join(
            grid_file_path, os.path.basename(rfile)), grid=grid)
    except Exception as e:
        print(f"Error processing file: {os.path.basename(rfile)}")
        print(str(e))


def process_file_wrapper(args):
    return process_file(*args)


if __name__ == "__main__":
    outdir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/GRID/IOP2/"
    basedir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/UAH_Mobile_Radar/"
    file_list = sorted(glob.glob(os.path.join(basedir, "RAW*2022033*nc")))
    print(f'Number of files: {len(file_list)}')
    global grid_file_path
    grid_file_path = os.path.join(outdir, "UAH")
    os.makedirs(grid_file_path, exist_ok=True)

    # Create a pool of worker processes
    pool = mp.Pool()

    # Map the data files to the process_file_wrapper function to process them in parallel
    results = pool.map(process_file_wrapper, [(outdir, f) for f in file_list])

    # Close the pool of worker processes
    pool.close()
    pool.join()
