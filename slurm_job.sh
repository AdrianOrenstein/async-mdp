#!/bin/bash
#SBATCH --account=def-mbowling
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=0-0:20

# cd /home/aorenste/projects/def-mbowling/aorenste

# if [ "$SLURM_TMPDIR" == "" ]; then
    # ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3`
    # export ALL_PROXY=socks5h://localhost:8888
    # export HTTP_PROXY="socks5://127.0.0.1:8888"
    # export HTTPS_PROXY="socks5://127.0.0.1:8888"

    

    # cd /home/aorenste/projects/def-mbowling/aorenste
    # git clone https://github.com/AdrianOrenstein/async-mdp.git
    # poetry config virtualenvs.path /home/aorenste/projects/def-mbowling/aorenste/virtualenvs
    # cd async-mdp

    # module load python/3.10

    # poetry env use python3.10
    # poetry shell

    # python -m pip install pysocks --no-index

    # tar -czf venv.tar.gz ~/projects/def-mbowling/aorenste/virtualenvs/async-mdp-PEBw-NfQ-py3.10

    # /lustre03/project/6006068/aorenste/virtualenvs/async-mdp-PEBw-NfQ-py3.10/bin/python -m pip install pysocks --no-index

    
#     poetry install
#     pip install pysocks --no-index

#     poetry install
# fi

# SOCKS5 Proxy
if [ "$SLURM_TMPDIR" != "" ]; then
    echo "Setting up SOCKS5 proxy..."
    ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3`
    export ALL_PROXY=socks5h://localhost:8888
    echo "SOCKS5 proxy is set up"

    git config --global http.proxy 'socks5://127.0.0.1:8888'
    git clone https://github.com/AdrianOrenstein/async-mdp.git $SLURM_TMPDIR/async-mdp

    cp ~/projects/def-mbowling/aorenste/venv.tar.gz $SLURM_TMPDIR/
    cd $SLURM_TMPDIR
    tar -xzf venv.tar.gz

    module load python/3.10.13 # includes poetry
    poetry config virtualenvs.path $SLURM_TMPDIR/virtualenvs

    cd $SLURM_TMPDIR/async-mdp
    export PYTHONPATH=./src:.
    # source $SLURM_TMPDIR/virtualenvs/async-mdp-PEBw-NfQ-py3.10/bin/activate
    # make a python_venv command from $SLURM_TMPDIR/virtualenvs/async-mdp-PEBw-NfQ-py3.10/bin/python3.10
    export python_venv=$SLURM_TMPDIR/virtualenvs/async-mdp-PEBw-NfQ-py3.10/bin/python3.10
    # $python_venv -m pip install pysocks --no-index
    python -m pip install pysocks --no-index

    $python_venv src/dqn.py --num-envs 1 --env-id CartPole-v1 --total-timesteps 10_000 --wandb-entity the-orbital-mind --wandb-project-name beluga-async-mdp-performance-vs-steprate-cartpole-v1-300000 --track --learning_rate 0.00025 --buffer_size 10000 --gamma 0.99 --target_network_frequency 500 --batch_size 128 --start_e 1 --end_e 0.0 --exploration_fraction 0.25 --learning_starts 10000 --train_frequency 10 --seed 0 --async-datarate 0



    


    # echo "Setup Modules"
    # echo "\t cp venv.zip"
    # cp venv.zip $SLURM_TMPDIR/
    # echo "\t unzipping venv.zip"
    # unzip -q -n $SLURM_TMPDIR/venv.zip -d $SLURM_TMPDIR/
    # echo "\t deleting venv.zip"
    # rm $SLURM_TMPDIR/venv.zip

    # source $SLURM_TMPDIR/home/aorenste/.cache/pypoetry/virtualenvs/async-mdp-PEBw-NfQ-py3.10/bin/activate
    # echo "in virtual env"

    # python3.10 -m pip install pysocks --no-index

    # echo "cloning repo"
    # git config --global http.proxy 'socks5://127.0.0.1:8888'
    # git clone https://github.com/AdrianOrenstein/async-mdp.git $SLURM_TMPDIR/async-mdp

    # echo "running job"
    # # export HTTPS_PROXY="socks5h://localhost:8888"
    # cd $SLURM_TMPDIR/async-mdp
    # python3.10 $SLURM_TMPDIR/async-mdp/src/experiment_runner.py
fi
echo "done"



# WANDB_MODE=offline python3.10 $SLURM_TMPDIR/async-mdp/src/experiment_runner.py

# WANDB_MODE=offline $SLURM_TMPDIR/virtualenvs/async-mdp-PEBw-NfQ-py3.10/bin/python src/dqn.py --num-envs 1 --env-id CartPole-v1 --total-timesteps 10_000 --wandb-entity the-orbital-mind --wandb-project-name async-mdp-performance-vs-steprate-cartpole-v1-300000 --track --learning_rate 0.00025 --buffer_size 10000 --gamma 0.99 --target_network_frequency 500 --batch_size 128 --start_e 1 --end_e 0.0 --exploration_fraction 0.25 --learning_starts 10000 --train_frequency 10 --seed 0 --async-datarate 0