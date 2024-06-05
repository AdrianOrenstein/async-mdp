module load python/3.11.5 StdEnv/2023 gcc/12.3 opencv/4.9.0 swig && \
	ssh -q -N -T -f -D 8888 `echo $SSH_CONNECTION | cut -d " " -f 3` && \
	export ALL_PROXY=socks5h://localhost:8888

mkdir -p /tmp/adrian/virtualenvs && \
	cd /tmp/adrian/virtualenvs && \
	echo "making venv" && \
	virtualenv --no-download pyenv && \
	source pyenv/bin/activate && \
	echo "activated..." && \
	pip install requests[socks] --no-index && \
	echo "has socks..." && \
	pip install --no-cache-dir "gymnasium[classic-control]" "gymnasium[box2d]" numpy "stable_baselines3>=2.0.0a" tqdm tyro torch tensorboard wandb --index-url https://pypi.org/simple --extra-index-url https://download.pytorch.org/whl/cpu && \
	echo "finished installing packages" && \
	cd /tmp/adrian/ && \
	echo "zipping..." && \
	tar -czf venv.tar.gz virtualenvs && \
	echo "moving..." && \
	mv venv.tar.gz ~/project/def-mbowling/aorenste/ && \
	echo "cleaning up..." && \
	rm -fr /tmp/adrian

echo "done"