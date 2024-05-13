#!/bin/bash
#SBATCH --account=def-mbowling
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=0-2:59
#SBATCH --cpu-freq=Performance
#SBATCH --array=1-30%1

# setup and tear down takes .5-2 minutes.

module load python/3.10.13

if [ "$SLURM_TMPDIR" == "" ]; then
    exit 1
fi 

echo "Copying virtualenv..."
cp ~/projects/def-mbowling/aorenste/venv.tar.gz $SLURM_TMPDIR/
cd $SLURM_TMPDIR 
tar -xzf venv.tar.gz
rm venv.tar.gz

echo "Setting up SOCKS5 proxy..."
ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3`
export ALL_PROXY=socks5h://localhost:8888

echo "Cloning repo..."
git config --global http.proxy 'socks5://127.0.0.1:8888'
git clone --quiet https://github.com/AdrianOrenstein/async-mdp.git $SLURM_TMPDIR/project

# wait for background jobs to complete
echo "Waiting for background jobs to complete..."

echo "Exporting env variables"
export PYTHONPATH=$SLURM_TMPDIR/project/src:.
export python_venv=$SLURM_TMPDIR/virtualenvs/pyenv/bin/python3.10

echo "Running experiment..."
cd $SLURM_TMPDIR/project
$python_venv $@ --seed $SLURM_ARRAY_TASK_ID

echo "done"