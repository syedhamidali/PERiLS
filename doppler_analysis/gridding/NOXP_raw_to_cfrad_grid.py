import multiprocessing as mp
import time
import os
import glob
from matplotlib import pyplot as plt
import numpy as np
import pyart
import warnings
warnings.filterwarnings("ignore")


def get_file_list(directory):
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.startswith("NOX"):
                files.append(os.path.join(root, filename))
    files.sort()
    return files


def _drop_fields(radar):
    ''' Drop fields'''
    print("Dropping unnecessary fields \n")
    fields_to_drop = ['total_power', 'spectrum_width', 'specific_differential_phase']
    for field in fields_to_drop:
        if field in radar.fields:
            del radar.fields[field]
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

    texture = pyart.retrieve.calculate_velocity_texture(radar,
                                                        vel_field=vel_field,
                                                        wind_size=16,
                                                        check_nyq_uniform=False)
    radar.add_field('VT', texture, replace_existing=True)
    gatefilter = pyart.filters.GateFilter(radar)
    gatefilter.include_above(refl_field, refl_thresh)
    gatefilter.include_inside(refl_field, 0, 70)
#     gatefilter.exclude_outside("PHIDP", -180, 180)
    gatefilter.exclude_outside("differential_reflectivity", -8, 8)
    gatefilter.exclude_above("VT", 20)
    
    if ncp_thresh is not None:
        gatefilter.exclude_below(ncp_field, ncp_thresh)
    else:
        pass
    
    if rho_thresh is not None:
        gatefilter.exclude_below(rho_field, rho_thresh)
    else:
        pass
    
    radar.scan_type = b'ppi'
    radar = mask_data(radar, refl_field, gatefilter)
    radar = mask_data(radar, vel_field, gatefilter)

    # Dealias
    radar = dealiase(radar, vel_name=vel_field,
                     gatefilter=gatefilter, method=dealias_method)

    mask = np.ma.getmask(radar.fields[refl_field]['data'])

    # Drop some fields
    radar = _drop_fields(radar)

    # iterate through remaining fields
    skip_fields = ["normalized_coherent_power"]
    for field in radar.fields.keys():
        if any(field == skip_field for skip_field in skip_fields):
            continue
        radar.fields[field]['data'] = np.ma.masked_where(
            mask, radar.fields[field]['data'])

    return radar


def _rename_moms(radar):
    '''Rename fields if they exist'''

    if 'DBZ' in radar.fields:
        radar.fields['REF'] = radar.fields.pop('DBZ')
    if 'reflectivity' in radar.fields:
        radar.fields['REF'] = radar.fields.pop('reflectivity')
    if 'DBZH' in radar.fields:
        radar.fields['REF'] = radar.fields.pop('DBZH')
    if 'ref' in radar.fields:
        radar.fields['REF'] = radar.fields.pop('ref')
        
    if 'VELH' in radar.fields:
        radar.fields['VEL'] = radar.fields.pop('VELH')
    if 'VEL_F' in radar.fields:
        radar.fields['VEL'] = radar.fields.pop('VEL_F')
    if 'velocity' in radar.fields:
        radar.fields['VEL'] = radar.fields.pop('velocity')
        
    if 'ZDRC' in radar.fields:
        radar.fields['ZDR'] = radar.fields.pop('ZDRC')
    if 'differential_reflectivity' in radar.fields:
        radar.fields['ZDR'] = radar.fields.pop('differential_reflectivity')
        
    if 'RHOHV' in radar.fields:
        radar.fields['RHO'] = radar.fields.pop('RHOHV')
    if 'cross_correlation_ratio' in radar.fields:
        radar.fields['RHO'] = radar.fields.pop('cross_correlation_ratio')

    return radar


def linspace_range(start, stop, step):
    num = np.floor((stop - start) / step + 1)
    num-=1
    return int(num), num*step/2


def process_file(outdir, grid_file_path, CFRAD_DIR, rfile):
    try:
        print(f'Reading file: {os.path.basename(rfile)}')
        radar = pyart.io.read_sigmet(rfile)
        if radar.nsweeps > 3:
            print(f'Saving Cfradial in {CFRAD_DIR} as {os.path.basename(rfile).split(".RAW")[0]+".nc"}')
            cffile = os.path.join(CFRAD_DIR, os.path.basename(rfile).split(".RAW")[0]+".nc")
            pyart.io.write_cfradial(filename=cffile, radar=radar)
            refl_field = "reflectivity"
            vel_field = "velocity"
            ncp_field = "normalized_coherent_power"
            rho_field = "cross_correlation_ratio"
            refl_thresh = -5
            rho_thresh = None
            ncp_thresh = None
            radar = filter_data(radar,
                                refl_field,
                                refl_thresh,
                                vel_field,
                                ncp_field=ncp_field,
                                ncp_thresh=ncp_thresh,
                                rho_field=rho_field,
                                rho_thresh=rho_thresh,
                                dealias_method='region')

            radar = _rename_moms(radar)

            max_range = radar.range['data'].max()
            xy, rng = linspace_range(-max_range, max_range, 500)

            gfields = ['REF', 'VEL', 'ZDR', "RHO"]
            grid = pyart.map.grid_from_radars(radar, (41, xy, xy),
                                              ((0., 10e3), (-rng, rng),
                                               (-rng, rng)),
                                              weighting_function='Barnes2',
                                              fields=gfields)
            del radar
            print(f'Saving in {grid_file_path} as {os.path.basename(rfile).split(".RAW")[0]+".nc"}')
            # Write grid
            pyart.io.write_grid(filename=os.path.join(
                grid_file_path, os.path.basename(rfile).split(".RAW")[0]+".nc"), grid=grid)
        else:
            print(f'Not enough sweeps in {os.path.basename(rfile)} to process.')
    except Exception as e:
        print(f"Error processing file: {os.path.basename(rfile)}")
        print(str(e))


def process_file_wrapper(args):
    return process_file(*args)


if __name__ == "__main__":
    outdir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/GRID/IOP2/"
    basedir = "/depot/dawson29/data/Projects/PERiLS/obsdata/2022/NOXP/"
    file_list = get_file_list(basedir)
    num_files = len(file_list)
    print("Number of NOXP files:", num_files)
    grid_file_path = os.path.join(outdir, "NOXP")
    os.makedirs(grid_file_path, exist_ok=True)
    CFRAD_DIR = os.path.join(basedir, "cfrad")
    os.makedirs(CFRAD_DIR, exist_ok=True)

    # Create a pool of worker processes for DOW7
    pool = mp.Pool()
    results = pool.map(process_file_wrapper, [(outdir, grid_file_path, CFRAD_DIR, f) for f in file_list])
    pool.close()
    pool.join()