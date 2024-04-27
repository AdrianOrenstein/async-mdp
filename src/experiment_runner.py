import itertools
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
    total_timesteps=50_000, num_envs=1, env_name="CartPole-v0", num_seeds=10
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
        "wandb-project-name": "async-mdp-performance-vs-steprate",
        "track": True,
    }

    # avg_rate_for_dqn = 9000  # sps
    for seed in range(0, 10):
        for data_rate in range(1000, 1400 + 100, 100):
            run_config = defaults.copy()
            run_config.update({"seed": seed, "async-datarate": data_rate})
            yield run_config

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

    for env_name in ["CartPole-v0"]:
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

    with open("jobs.json", "w") as f:
        json.dump(all_jobs, f)

    # run all jobs, popping them off the list as they finish
    while len(all_jobs) > 0:
        job_UID, job_dic = all_jobs.popitem()
        print(f"Running job {job_UID}")
        subprocess.run(job_dic["command"], shell=True)

        # write all jobs to a json to record completeness
        with open("jobs.json", "w") as f:
            json.dump(all_jobs, f)
