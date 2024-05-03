#!/bin/bash
#SBATCH --account=def-mbowling
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=0-0:15

cd /home/aorenste/projects/def-mbowling/aorenste

# SOCKS5 Proxy
if [ "$SLURM_TMPDIR" != "" ]; then
    echo "Setting up SOCKS5 proxy..."
    ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3`
    export ALL_PROXY=socks5h://localhost:8888
    echo "SOCKS5 proxy is set up"

    echo "Setup Modules"
    echo "\t cp venv.zip"
    cp venv.zip $SLURM_TMPDIR/
    echo "\t unzipping venv.zip"
    unzip -q -n $SLURM_TMPDIR/venv.zip -d $SLURM_TMPDIR/
    echo "\t deleting venv.zip"
    rm $SLURM_TMPDIR/venv.zip

    source $SLURM_TMPDIR/home/aorenste/.cache/pypoetry/virtualenvs/async-mdp-PEBw-NfQ-py3.10/bin/activate
    echo "in virtual env"

    python3.10 -m pip install pysocks --no-index

    echo "cloning repo"
    git config --global http.proxy 'socks5://127.0.0.1:8888'
    git clone https://github.com/AdrianOrenstein/async-mdp.git $SLURM_TMPDIR/async-mdp

    echo "running job"
    # export HTTPS_PROXY="socks5h://localhost:8888"
    cd $SLURM_TMPDIR/async-mdp
    python3.10 $SLURM_TMPDIR/async-mdp/src/experiment_runner.py
fi
echo "done"



# WANDB_MODE=offline python3.10 $SLURM_TMPDIR/async-mdp/src/experiment_runner.py