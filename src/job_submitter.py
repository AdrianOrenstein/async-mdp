import itertools
import math
import os


def convert_job_dic_to_key(job_dic: dict) -> str:
    job_params = []

    banned_keys = ["command", "wandb-entity", "wandb-project-name", "track"]

    for i, (k, v) in enumerate(job_dic.items()):
        if k in banned_keys:
            continue

        if type(v) == bool:
            job_params.append(f"{k}")
        else:
            job_params.append(f"{k}-{v}")

    return (
        "--".join(job_params)
        .replace("_", "")
        .replace(" ", "")
        .replace("/", "")
        .replace(".py", "")
    )


def observing_steprate_over_training(
    total_timesteps=50_000, num_envs=1, env_name="CartPole-v0"
):
    defaults = {
        "algo": "src/dqn.py",
        "num-envs": num_envs,
        "env-id": env_name,
        "total-timesteps": total_timesteps,
        "wandb-entity": "the-orbital-mind",
        "wandb-project-name": "async-mdp-observe-steprate",
        "track": True,
    }

    # avg_rate_for_dqn = 9000  # sps
    for seed in range(0, 10):
        run_config = defaults.copy()
        run_config.update({"seed": seed})
        yield run_config


def simplified_async_interface_with_dqn(env_name="CartPole-v1", num_seeds=10):
    """
    We've computed the average datarate of DQN for the basic control environments which is about 9300 sps.
    Now we want to start at around that rate and move up and down by 1000 sps.

    For each environment, we run num_seeds runs with a single environment for each. We also test both async and sync to compare results.
    """

    defaults = {
        "algo": "src/dqn.py",
        "num-envs": 1,
        "env-id": env_name,
        "wandb-entity": "the-orbital-mind",
        "wandb-project-name": "-".join(
            [
                os.getenv("SLURM_CLUSTERID") or "na",
                "simplified-async-interface-with-dqn",
                env_name.lower(),
            ]
        ),
        "track": True,
    }

    # DQN hyperparams
    defaults.update(
        {
            "total-timesteps": 300_000,
            "learning_rate": 0.003,
            "buffer_size": 10_000,
            "gamma": 0.99,
            "target_network_frequency": 500,
            "batch_size": 128,
            "start_e": 1,
            "end_e": 0.05,
            "exploration_fraction": 0.25,
            "learning_starts": 10_000,
            "train_frequency": 10,
        }
    )

    algo_kwargs = {
        "MountainCar-v0": {"learning_rate": 0.003},
        "CartPole-v1": {"learning_rate": 0.0003},
        "Acrobot-v1": {"learning_rate": 0.003},
    }

    def experiment_run(defaults, seed, data_rate=None, num_repeat_actions=None):
        run_config = defaults.copy()

        # copy over env specific params
        if env_name in algo_kwargs:
            run_config.update(algo_kwargs[env_name])

            # update project name because we're changing the problem
            run_config["wandb-project-name"] = "-".join(
                [
                    run_config["wandb-project-name"],
                    str(run_config.get("total-timesteps")),
                ]
            )

        if os.getenv("DONT_SUBMIT_SEEDS") != "1":
            run_config.update({"seed": seed})

        if data_rate is not None:
            run_config.update({"async-datarate": data_rate})

        if num_repeat_actions is not None:
            run_config.update({"num-repeat-actions": num_repeat_actions})

        yield run_config

    for seed in range(0, num_seeds):
        # async problem
        for data_rate in range(2_000, 45_000 + 1000, 1000):
            yield from experiment_run(defaults=defaults, seed=seed, data_rate=data_rate)

        # simulating the async problem
        for repeat_actions in range(0, 25 + 1):
            yield from experiment_run(
                defaults=defaults, seed=seed, num_repeat_actions=repeat_actions
            )

        # no async wrapper
        yield from experiment_run(defaults=defaults, seed=seed)


def seconds_to_hms(seconds: float):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"


if __name__ == "__main__":
    ENV_NAMES = ["CartPole-v1", "MountainCar-v0", "Acrobot-v1"]
    EXPERIMENTS = {
        # "observing_steprate_over_training": observing_steprate_over_training,
        # "changing_datarate_for_DQN": changing_datarate_for_DQN,
        "simplified_async_interface_with_dqn": simplified_async_interface_with_dqn,
    }

    experiment_name = "simplified_async_interface_with_dqn"

    all_jobs = {}

    for env_name in ENV_NAMES:
        for job_dic in EXPERIMENTS[experiment_name](env_name=env_name):
            job_UID = "-".join(
                (
                    str(i)
                    for i in [
                        job_dic.get("num-repeat-actions", "na"),
                        job_dic.get("async-datarate", "na"),
                        job_dic.get("learning_rate"),
                        experiment_name.replace("_", ""),
                        job_dic.get("env-id"),
                    ]
                )
            )
            if os.getenv("DONT_SUBMIT_SEEDS") != "1":
                job_UID += f"-{job_dic.get('seed')}"

            run_list = ["poetry", "run", "python", job_dic["algo"]]
            if os.getenv("SLURM_CLUSTERID") != "m1_mac":
                run_list = [
                    "sbatch",
                    f"--job-name {job_UID}",
                    "./slurm_job.sh",
                    job_dic["algo"],
                ]

            job_dic.update(
                {
                    "command": " ".join(
                        run_list
                        + [
                            f"--{k} {v}" if type(v) != bool else f"--{k}"
                            for k, v in job_dic.items()
                            if k != "algo"
                        ]
                    ),
                }
            )

            print(job_UID, job_dic)

            all_jobs.update({job_UID: job_dic})

            if int(os.getenv("DEBUG", default=0)) > 1:
                print(job_UID)
                for k, v in job_dic.items():
                    print(f"\t{k}: {v}")

    print(len(all_jobs))
    import subprocess

    # write all jobs to a json to record completeness
    import json

    print(f"Total number of jobs: {len(all_jobs)}")
    # Load or initialize the job completion record
    try:
        with open("jobs.json", "r") as f:
            completed_jobs = json.load(f)
    except FileNotFoundError:
        completed_jobs = {}

    if int(os.getenv("DEBUG", default=0)) > 0:
        # print command of first job and exit
        print(all_jobs[list(all_jobs.keys())[0]]["command"])
        exit()

    # Run all jobs that are not marked as completed
    for job_UID, job_dic in all_jobs.items():
        if job_UID not in completed_jobs:

            # check if we're on the slurm cluster
            # if os.getenv("IS_SLURM"):
            # time_for_experiment = 120 + max(job_dic["command"].get("total-timesteps")/100, math.ceil(job_dic["command"].get("total-timesteps") / job_dic["command"].get("async-datarate")))
            # print(f"Running on slurm, setting time to {seconds_to_hms(time_for_experiment)}")
            # job_dic["command"] = f"sbatch --job ./slurm_job.sh {job_dic['command']}"

            print(f"Submitting job {job_UID}")
            # print(f"\t{job_dic['command']}")
            process = subprocess.run(
                job_dic["command"], shell=True, check=True, capture_output=True
            )

            # Mark the job as completed
            completed_jobs[job_UID] = process.returncode

            # Write the updated completion status to the JSON file
            with open("jobs.json", "w") as f:
                json.dump(completed_jobs, f)

            print(
                f"Job {job_UID} completed with return code {process.returncode}, saved to jobs.json"
            )

        else:
            print(f"Skipping completed job {job_UID}")

# SLURM_CLUSTERID=m1_mac PYTHONPATH=./src:. poetry run python src/job_submitter.py
# DONT_SUBMIT_SEEDS=1 SLURM_CLUSTERID=beluga_4cpu_perf_arrayjob_final python src/job_submitter.py
