module load python/3.10
git clone https://github.com/AdrianOrenstein/async-mdp.git ~/projects/def-mbowling/aorenste/
pip install pysocks --no-index
cd ~/projects/def-mbowling/aorenste/async-mdp


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