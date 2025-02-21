import multiprocessing as mp
import time
import os
import glob
from matplotlib import pyplot as plt
from pyart.retrieve import get_freq_band
import numpy as np
import pyart
import warnings
warnings.filterwarnings("ignore")
# from pymeso import llsd
# import scipy


def get_file_list(directory):
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    files.sort()
    return files


def _drop_fields(radar):
    fields_to_drop = ["DBMHC", "DBMVC", "VS", "VS_F", "VL", "VL_F", "DBZHCC", "ZDR", "WIDTH",
                      "SNRVC", 'DBZHC_F', 'DBZVC', 'DBZVC_F', 'VEL',]
    for field in fields_to_drop:
        if field in radar.fields:
            del radar.fields[field]
    return radar


def _align_field(field):
    values, counts = np.unique(field['data'], return_counts=True)
    c_value = values[np.argmax(counts)]
    field['data'] = np.array([c_value])
    return field


def align_radar_coords(radar):
    for field_name in ['longitude', 'latitude', 'altitude', 'altitude_agl']:
        setattr(radar, field_name, _align_field(getattr(radar, field_name)))
    return radar


def mask_data(radar, field, gatefilter):
    dsp = pyart.correct.despeckle_field(
        radar, field, gatefilter=gatefilter, size=15)
    new_field = radar.fields[field].copy()
    new_field['data'] = np.ma.masked_where(
        dsp.gate_included == False, radar.fields[field]['data'])
    radar.add_field(field, new_field, replace_existing=True)
    return radar


# function to dealiase the Doppler velocity
def dealiase(radar, vel_name='VEL_F', gatefilter=None, method="unwrap"):
    '''
    Dealias Doppler velocities using Py-ART.
    method : str
        Method to use for the dealiasing. Can be 'unwrap' or 'region'.
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


def filter_data(radar, refl_field, refl_thresh, vel_field,
                ncp_field=None, ncp_thresh=None,
                rho_field=None, rho_thresh=None,
                dealias_method="region"):
    '''Remove noise based on velocity texture,snr, and rhohv, and mask all the fields'''

    # Align radar coords
    radar = align_radar_coords(radar)

#     if ncp_field is None or ncp_thresh is None:
#         ncp_field = "NCP"
#         ncp_thresh = 0.1

#     # Set default values if rho_field or rho_thresh are None
#     if rho_field is None or rho_thresh is None:
#         rho_field = "RHOHV"
#         rho_thresh = 0.5

    texture = pyart.retrieve.calculate_velocity_texture(radar,
                                                        vel_field=vel_field,
                                                        wind_size=16,
                                                        check_nyq_uniform=False
                                                        )

    radar.add_field('VT', texture, replace_existing=True)
    gatefilter = pyart.filters.GateFilter(radar)
    gatefilter.include_above(refl_field, refl_thresh)
    gatefilter.include_inside(refl_field, 10, 70)
    gatefilter.exclude_above("TRIP_FLA", 1)
#     gatefilter.exclude_outside("PHIDP", -180, 180)
#     gatefilter.exclude_outside("ZDRC", -8, 8)
    gatefilter.include_above("SNRHC", -5)
    gatefilter.exclude_below("SNRHC", -6)
    gatefilter.exclude_above("VT", 30)
    if ncp_thresh is not None:
        gatefilter.exclude_below(ncp_field, ncp_thresh)
    else:
        pass
    if rho_thresh is not None:
        gatefilter.exclude_below(rho_field, rho_thresh)
    else:
        pass
    radar.scan_type = 'ppi'
    radar = mask_data(radar, refl_field, gatefilter)
    radar = mask_data(radar, vel_field, gatefilter)

    # Dealias
    radar = dealiase(radar, vel_name=vel_field,
                     gatefilter=gatefilter, method=dealias_method)

    # call the llsd function form llsd.py
#     az_shear_meta = llsd.main(radar, refl_field, vel_field, window_size = (1200, 3600))
#     radar.add_field('AZS', az_shear_meta, replace_existing=True)

    # mask the field
    mask = np.ma.getmask(radar.fields[refl_field]['data'])

    # Drop some fields
    radar = _drop_fields(radar)

    # iterate through remaining fields
    skip_fields = ["DBZHC", "VEL", "VEL_F"]
    for field in radar.fields.keys():
        if any(field == skip_field for skip_field in skip_fields):
            continue
        radar.fields[field]['data'] = np.ma.masked_where(
            mask, radar.fields[field]['data'])

    return radar


def _rename_moms(radar):
    '''Rename fields'''
    radar.fields['REF'] = radar.fields.pop('DBZHCC_F')
    radar.fields['VEL'] = radar.fields.pop('VEL_F')
    radar.fields['ZDR'] = radar.fields.pop('ZDRC')
    radar.fields['RHO'] = radar.fields.pop('RHOHV')

    return radar


def process_file(outdir, rfile):
    try:
        print(f'Reading file: {os.path.basename(rfile)}')
        radar = pyart.io.read(rfile)
        refl_field = "DBZHCC_F"
        vel_field = "VEL_F"
        ncp_field = "NCP"
        refl_thresh = 5
        ncp_thresh = None
        rho_field = "RHOHV"
        rho_thresh = 0.5
        radar = filter_data(radar, refl_field,
                            refl_thresh=refl_thresh,
                            vel_field=vel_field,
                            ncp_field=ncp_field,
                            ncp_thresh=ncp_thresh,
                            rho_field=rho_field,
                            rho_thresh=rho_thresh,
                            dealias_method='region',
                            )
        radar = _rename_moms(radar)
        max_rng = 88.25*1e3
        grid = pyart.map.grid_from_radars(radar, (41, 354, 354),
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
    basedir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/Illinois_Mobile_Radar/IOP2/"
    cow_dir = os.path.join(basedir, "COW1/merged/")
    file_list = get_file_list(cow_dir)
    num_files = len(file_list)
    print("Number of files:", num_files)
    global grid_file_path
    grid_file_path = os.path.join(outdir, "COW1")
    os.makedirs(grid_file_path, exist_ok=True)

    # Create a pool of worker processes
    pool = mp.Pool()

    # Map the data files to the process_file_wrapper function to process them in parallel
    results = pool.map(process_file_wrapper, [(outdir, f) for f in file_list])

    # Close the pool of worker processes
    pool.close()
    pool.join()
