#!/bin/bash
#SBATCH -A dawson29
#SBATCH --job-name=dask_gridding
#SBATCH --output=out_test_dask_gridding.out
#SBATCH --error=out_test_dask_gridding.err
#SBATCH --nodes=4
#SBATCH --cpus-per-task=100
#SBATCH --time=02:00:00

# Print the hostname of the compute node on which this job is running.
/bin/hostname


module use /depot/dawson29/data/Projects/PERiLS/etc/modules/
module load conda-env/perils-py3.8.5

python /home/syed44/PERiLS/doppler_analysis/gridding/test_dask_gridding.py