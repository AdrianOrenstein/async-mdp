TEMP_DIR=$(mktemp -d /tmp/async-proj-$(date +%s))
echo "temp dir: $TEMP_DIR"

USER="aorenste"
GROUP="def-mbowling"

module load python/3.11 StdEnv/2023 gcc opencv/4.8.1 swig && \
	ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3` && \
	export ALL_PROXY=socks5h://localhost:8888

mkdir -p $TEMP_DIR/virtualenvs && \
	cd $TEMP_DIR/virtualenvs && \
	# 
	echo "making venv" && \
	virtualenv --no-download pyenv && \
	source pyenv/bin/activate && \
	# 
	echo "activated..." && \
	pip install 'requests[socks]' --no-index && \
	pip install --no-cache-dir minigrid gymnasium "gymnasium[classic-control,box2d,atari,other]" filelock pillow autorom "numpy<2" "stable_baselines3==2.0.0a1" tqdm tyro torch tensorboard wandb --index-url https://pypi.org/simple && \
	AutoROM -y && \ 
	# 
	cd $TEMP_DIR && \
	echo "zipping..." && \
	tar -czf pfrlenv.tar.gz virtualenvs && \
	# 
	echo "moving..." && \
	mv pfrlenv.tar.gz ~/projects/$GROUP/$USER/ && \
	# 
	echo "cleaning up..." && \
	rm -fr $TEMP_DIR

echo "done"
