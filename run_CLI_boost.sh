arg1=$1
arg2=$2

module purge
module load python
conda activate /dls/science/groups/i23/pyenvs/carelesspy_3p9
python3 /dls/science/groups/i23/scripts/chris/careless_guimore/CLI_boost.py $arg1 $arg2
