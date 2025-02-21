#!/bin/bash
#SBATCH -A dawson29
#SBATCH --job-name=test_concurrent_griddding
#SBATCH --output=out_test_concurrent_griddding.out
#SBATCH --nodes=4
#SBATCH --cpus-per-task=100
#SBATCH --time=02:00:00
#SBATCH --qos=high

# Print the hostname of the compute node on which this job is running.
/bin/hostname


module use /depot/dawson29/data/Projects/PERiLS/etc/modules/
module load conda-env/perils-py3.8.5

python /home/syed44/PERiLS/doppler_analysis/gridding/test_concurrent_griddding.py