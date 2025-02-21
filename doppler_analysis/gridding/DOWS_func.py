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
    ''' Drop fields'''
    print("Dropping unnecessary fields \n")
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
    print("Aligning coordinates \n")
    for field_name in ['longitude', 'latitude', 'altitude', 'altitude_agl']:
        setattr(radar, field_name, _align_field(getattr(radar, field_name)))
    return radar


def mask_azimuth_jumps(radar):
    '''Mask Azimuth Jumps'''
    print("Masking azimuth jumps \n")
    az_diff = np.diff(radar.azimuth['data'])
    jumps = np.where((np.abs(az_diff) >= 10) & (np.abs(az_diff) < 359))[0]

    if len(jumps):
        for field in radar.fields.keys():
            for jump in jumps:
                radar.fields[field]['data'][jump].mask = True

    # Mask fields where azimuth is greater than 90 and less than 100
    azimuth = radar.azimuth['data']
    azimuth_mask = np.logical_and(azimuth > 92, azimuth < 125)
    for field in radar.fields.keys():
        radar.fields[field]['data'][azimuth_mask] = np.ma.masked

    return radar


def mask_data(radar, field, gatefilter):
    print(f'Masking: {field} \n')
    dsp = pyart.correct.despeckle_field(
        radar, field, gatefilter=gatefilter, size=15)
    new_field = radar.fields[field].copy()
    new_field['data'] = np.ma.masked_where(
        dsp.gate_included == False, radar.fields[field]['data'])
    radar.add_field(field, new_field, replace_existing=True)
    return radar


# function to dealiase the Doppler velocity
def dealiase(radar, vel_name='VEL_F', gatefilter=None, method="region"):
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
    
    if radar.metadata['instrument_name'] == 'DOW7high':
        radar = mask_azimuth_jumps(radar)

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
    gatefilter.exclude_above("VT", 20)
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
    '''Rename fields if they exist'''

    if 'DBZHCC_F' in radar.fields:
        radar.fields['REF'] = radar.fields.pop('DBZHCC_F')
    if 'VEL_F' in radar.fields:
        radar.fields['VEL'] = radar.fields.pop('VEL_F')
    if 'ZDRC' in radar.fields:
        radar.fields['ZDR'] = radar.fields.pop('ZDRC')
    if 'RHOHV' in radar.fields:
        radar.fields['RHO'] = radar.fields.pop('RHOHV')

    return radar


def process_file(outdir, grid_file_path, rfile):
    try:
        print(f'Reading file: {os.path.basename(rfile)}')
        radar = pyart.io.read(rfile)
        refl_field = "DBZHCC_F"
        vel_field = "VEL_F"
        ncp_field = "NCP"
        rho_field = "RHOHV"
        refl_thresh = -5

        if radar.metadata['instrument_name'] == 'DOW8':
            ncp_thresh = 0.05
        else:
            ncp_thresh = None

        if radar.metadata['instrument_name'] == 'DOW7high':
            rho_thresh = 0.1
        else:
            rho_thresh = None

        radar = filter_data(radar, refl_field,
                            refl_thresh=refl_thresh,
                            vel_field=vel_field,
                            ncp_field=ncp_field,
                            ncp_thresh=ncp_thresh,
                            rho_field=rho_field,
                            rho_thresh=rho_thresh,
                            dealias_method='region',
                            )
        if radar.metadata['instrument_name'] == 'DOW7high':
            radar = _rename_moms(radar)
            max_rng = 74750.0
            xy = 299
            gfields = ['REF', 'VEL', 'ZDR', "RHO"]
        if radar.metadata['instrument_name'] == 'DOW8':
            radar = _rename_moms(radar)
            max_rng = 73.5*1e3
            xy = 294
            gfields = ['REF', 'VEL']
        grid = pyart.map.grid_from_radars(radar, (41, xy, xy),
                                          ((0., 10e3), (-max_rng, max_rng),
                                           (-max_rng, max_rng)),
                                          weighting_function='Barnes2',
                                          fields=gfields)

        print(f'Deleting Radar Object: {os.path.basename(rfile)} \n')
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

#     # First directory (DOW8)
#     dow8_dir = os.path.join(basedir, "DOW8/merged/")
#     file_list_dow8 = get_file_list(dow8_dir)
#     num_files_dow8 = len(file_list_dow8)
#     print("Number of files in DOW8 directory:", num_files_dow8)
#     grid_file_path_dow8 = os.path.join(outdir, "DOW8")
#     os.makedirs(grid_file_path_dow8, exist_ok=True)

    # Second directory (DOW7)
    dow7_dir = os.path.join(basedir, "DOW7/merged/")
    file_list_dow7 = get_file_list(dow7_dir)
    num_files_dow7 = len(file_list_dow7)
    print("Number of files in DOW7 directory:", num_files_dow7)
    grid_file_path_dow7 = os.path.join(outdir, "DOW7")
    os.makedirs(grid_file_path_dow7, exist_ok=True)

#     # Create a pool of worker processes for DOW8
#     pool_dow8 = mp.Pool()
#     results_dow8 = pool_dow8.map(process_file_wrapper, [(outdir, grid_file_path_dow8, f) for f in file_list_dow8])
#     pool_dow8.close()
#     pool_dow8.join()

    # Create a pool of worker processes for DOW7
    pool_dow7 = mp.Pool()
    results_dow7 = pool_dow7.map(process_file_wrapper, [(outdir, grid_file_path_dow7, f) for f in file_list_dow7])
    pool_dow7.close()
    pool_dow7.join()
