#!/bin/sh -l
# FILENAME:  gridding2

#SBATCH -A dawson29

#SBATCH -o /home/syed44/PERiLS/doppler_analysis/gridding/gridding2.out

#SBATCH --nodes=1
#SBATCH -c 32
#SBATCH --time=72:00:00


# Print the hostname of the compute node on which this job is running.
/bin/hostname


module use /depot/dawson29/data/Projects/PERiLS/etc/modules/
module load conda-env/perils-py3.8.5

python /home/syed44/PERiLS/doppler_analysis/gridding/NEXRAD_gridding-Copy2.py