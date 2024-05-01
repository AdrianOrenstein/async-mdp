import itertools
import os
from loguru import logger


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
    total_timesteps=50_000, num_envs=1, env_name="CartPole-v0", num_seeds=10
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


def changing_datarate_for_DQN(
    total_timesteps=50_000, num_envs=1, env_name="CartPole-v1", num_seeds=30
):
    """
    We've computed the average datarate of DQN for the basic control environments which is about 9300 sps.
    Now we want to start at around that rate and move up and down by 1000 sps.

    For each environment, we run num_seeds runs with a single environment for each. We also test both async and sync to compare results.
    """

    defaults = {
        "algo": "src/dqn.py",
        "num-envs": num_envs,
        "env-id": env_name,
        "total-timesteps": total_timesteps,
        "wandb-entity": "the-orbital-mind",
        "wandb-project-name": "-".join(
            ["async-mdp-performance-vs-steprate", env_name.lower()]
        ),
        "track": True,
    }

    # DQN hyperparams
    defaults.update(
        {
            "learning_rate": 2.5e-4,
            "buffer_size": 10_000,
            "gamma": 0.99,
            "target_network_frequency": 500,
            "batch_size": 128,
            "start_e": 1,
            "end_e": 0.00,
            "exploration_fraction": 0.25,
            "learning_starts": 10_000,
            "train_frequency": 10,
        }
    )

    algo_kwargs = {
        "MountainCar-v0": {
            "total-timesteps": 300_000,
            # "learning_rate": 4e-3,
            # "gamma": 0.99,
            # "target_network_frequency": 600,
            # "end_e": 0.07,
            # "exploration_fraction": 0.2,
            # "learning_starts": 1_000,
            # "train_frequency": 16,
        },
        "CartPole-v1": {
            "total-timesteps": 300_000,
        },
        "Acrobot-v1": {
            "total-timesteps": 300_000,
        },
    }

    def experiment_run(defaults, seed, data_rate):
        run_config = defaults.copy()

        # copy over env specific params
        if env_name in algo_kwargs:
            run_config.update(algo_kwargs[env_name])

            # update project name because we're changing the problem
            run_config["wandb-project-name"] = "-".join(
                [
                    run_config["wandb-project-name"],
                    str(algo_kwargs[env_name].get("total-timesteps")),
                ]
            )

        run_config.update({"seed": seed, "async-datarate": data_rate})

        yield run_config

    # Using AsyncWrapper, 0 = env waits for the agent.
    for seed in range(0, num_seeds):
        yield from experiment_run(defaults=defaults, seed=seed, data_rate=0)

    for seed in range(0, num_seeds):
        for data_rate in range(1000, 3000 + 100, 100):
            yield from experiment_run(defaults=defaults, seed=seed, data_rate=data_rate)

    # for seed in range(0, num_seeds):
    #     run_config = defaults.copy()
    #     run_config.update({"seed": seed})
    #     yield run_config


if __name__ == "__main__":
    ENV_NAMES = ["CartPole-v1", "MountainCar-v0", "Acrobot-v1"]
    EXPERIMENTS = {
        "observing_steprate_over_training": observing_steprate_over_training,
        "changing_datarate_for_DQN": changing_datarate_for_DQN,
    }

    experiment_name = "changing_datarate_for_DQN"

    all_jobs = {}

    for env_name in ENV_NAMES:
        for job_dic in EXPERIMENTS[experiment_name](env_name=env_name):
            job_UID = f"{experiment_name.replace('_', '')}--" + convert_job_dic_to_key(
                job_dic
            )

            job_dic.update(
                {
                    "command": " ".join(
                        ["poetry", "run", "python", job_dic["algo"]]
                        + [
                            f"--{k} {v}" if type(v) != bool else f"--{k}"
                            for k, v in job_dic.items()
                            if k != "algo"
                        ]
                    ),
                }
            )

            all_jobs.update({job_UID: job_dic})

            if int(os.getenv("DEBUG", default=0)) > 0:
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

    # Run all jobs that are not marked as completed
    for job_UID, job_dic in all_jobs.items():
        if job_UID not in completed_jobs:

            logger.info(f"Running job {job_UID}")
            print(f"\t{job_dic['command']}")
            process = subprocess.run(
                job_dic["command"], shell=True, check=True, capture_output=True
            )

            # Mark the job as completed
            completed_jobs[job_UID] = process.returncode

            # Write the updated completion status to the JSON file
            with open("jobs.json", "w") as f:
                json.dump(completed_jobs, f)

            logger.success(
                f"Job {job_UID} completed with return code {process.returncode}, saved to jobs.json"
            )

        else:
            logger.info(f"Skipping completed job {job_UID}")
