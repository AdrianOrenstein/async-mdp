#!/bin/bash
#SBATCH --account=def-mbowling
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=0-2:59
#SBATCH --cpu-freq=Performance
#SBATCH --array=11-30

# setup and tear down takes .5-2 minutes.

module load python/3.10.13

if [ "$SLURM_TMPDIR" == "" ]; then
    exit 1
fi 

cd /home/aorenste/projects/def-mbowling/aorenste/

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
export python_venv=$SLURM_TMPDIR/virtualenvs/async-mdp-PEBw-NfQ-py3.10/bin/python3.10

echo "Running experiment..."
cd $SLURM_TMPDIR/project
$python_venv $@ --seed $SLURM_ARRAY_TASK_ID
    # && \ 
    # echo "Syncing wandb..." && \ 
    # $python_venv -m wandb sync $SLURM_TMPDIR/project/wandb/

# WANDB_MODE=offline $python_venv src/dqn.py --num-envs 1 --env-id CartPole-v1 --total-timesteps 10_000 --wandb-entity the-orbital-mind --wandb-project-name beluga-async-mdp-performance-vs-steprate-cartpole-v1-300000 --track --learning_rate 0.00025 --buffer_size 10000 --gamma 0.99 --target_network_frequency 500 --batch_size 128 --start_e 1 --end_e 0.0 --exploration_fraction 0.25 --learning_starts 10000 --train_frequency 10 --seed 0 --async-datarate 1000 && \ 


echo "done"