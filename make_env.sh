module load python/3.10.13 swig
ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3`
export ALL_PROXY=socks5h://localhost:8888
export HTTP_PROXY=socks5h://localhost:8888
export HTTPS_PROXY=socks5h://localhost:8888
git config --global http.proxy 'socks5://127.0.0.1:8888'

# mkdir -p $SLURM_TMPDIR
git clone https://github.com/AdrianOrenstein/async-mdp.git $SLURM_TMPDIR/project

cd $SLURM_TMPDIR/virtualenvs && virtualenv pyenv
. pyenv/bin/activate
pip install requests[socks] --no-index
pip install gymnasium gymnasium[classic-control] gymnasium[box2d] numpy "stable_baselines3==2.0.0a1" tqdm tyro torch tensorboard wandb --index-url https://download.pytorch.org/whl/cpu

PYTHONPATH=$SLURM_TMPDIR/project/src:. $SLURM_TMPDIR/virtualenvs/pyenv/bin/python3.10 src/dqn.py --num-envs 1 --env-id Acrobot-v1 --wandb-entity the-orbital-mind --wandb-project-name testing --track --total-timesteps 300000 --learning_rate 0.003 --buffer_size 10000 --gamma 0.99 --target_network_frequency 500 --batch_size 128 --start_e 1 --end_e 0.05 --exploration_fraction 0.25 --learning_starts 10000 --train_frequency 10
# python src/dqn.py --num-envs 1 --env-id Acrobot-v1 --wandb-entity the-orbital-mind --wandb-project-name testing --track --total-timesteps 300000 --learning_rate 0.003 --buffer_size 10000 --gamma 0.99 --target_network_frequency 500 --batch_size 128 --start_e 1 --end_e 0.05 --exploration_fraction 0.25 --learning_starts 10000 --train_frequency 10

tar -czf venv.tar.gz $SLURM_TMPDIR/virtualenvs


# module load python/3.10
# ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3`
# export ALL_PROXY=socks5h://localhost:8888
# export HTTP_PROXY=socks5h://localhost:8888
# export HTTPS_PROXY=socks5h://localhost:8888
# git config --global http.proxy 'socks5://127.0.0.1:8888'
# # git clone https://github.com/AdrianOrenstein/async-mdp.git ~/projects/def-mbowling/aorenste/test/project
# # poetry config virtualenvs.path ~/projects/def-mbowling/aorenste/virtualenvs
# git clone https://github.com/AdrianOrenstein/async-mdp.git /tmp/adrian/project
# poetry config virtualenvs.path /tmp/adrian/virtualenvs
# cd /tmp/adrian/project
# poetry env use python3.10
# poetry install
# export python_venv=$(poetry shell)
# $python_venv -m pip install requests[socks]
# tar -czf venv.tar.gz ~/projects/def-mbowling/aorenste/test/virtualenvs

z

# # save python virtual env dir
# python_venv=${which python}
# # get pysocks for later
# $python_venv -m pip install pysocks --no-index
# # zip up our virtual env
# 

# cd /home/aorenste/projects/def-mbowling/aorenste

# if [ "$SLURM_TMPDIR" == "" ]; then
    # ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3`


    

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