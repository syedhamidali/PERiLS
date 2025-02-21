#!/bin/sh -l
# FILENAME:  quality_check

#SBATCH -A dawson29

#SBATCH -o /home/syed44/PERiLS/doppler_analysis/farm_iop1_qc.out

#SBATCH --nodes=2
#BATCH -c 16
#SBATCH --time=72:00:00
#SBATCH --mem=25000

# Print the hostname of the compute node on which this job is running.
/bin/hostname


module use /depot/dawson29/data/Projects/PERiLS/etc/modules/
module load conda-env/perils-py3.8.5

python quality_check_script.py