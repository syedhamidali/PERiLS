#!/bin/sh -l
# FILENAME:  gridding2

#SBATCH -A dawson29

#SBATCH -o /home/syed44/PERiLS/doppler_analysis/gridding/parallel_gridding.out

#SBATCH --nodes=1
#SBATCH -c 128
#SBATCH --time=03:00:00
#SBATCH --mail-user=syed44@purdue.edu
#SBATCH --mail-type=BEGIN,END


# Print the hostname of the compute node on which this job is running.
/bin/hostname


module use /depot/dawson29/data/Projects/PERiLS/etc/modules/
module load conda-env/perils-py3.8.5

python /home/syed44/PERiLS/doppler_analysis/gridding/NOXP_raw_to_cfrad_grid.py