# docs and experiment results can be found at https://docs.cleanrl.dev/rl-algorithms/dqn/#dqnpy
import os
import random
import time
from dataclasses import dataclass

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import tyro
from stable_baselines3.common.buffers import ReplayBuffer
from torch.utils.tensorboard import SummaryWriter
from simple_asyncmdp import AsynchronousGym

from tqdm import tqdm

"""
poetry run python src/dqn.py \
    --seed 4 \
    --num-envs 1 \
    --env-id CartPole-v0 \
    --total-timesteps 50_000
    
    
poetry run python src/dqn.py \
    --seed 1 \
    --num-envs 1 \
    --async-datarate 100 \
    --env-id CartPole-v0 \
    --total-timesteps 50_000 \
    --wandb-entity "the-orbital-mind" \
    --wandb-project-name "test-async-mdp" \
    --track
    
    
    
Experiment
poetry run python src/dqn.py \
    --seed 1 \
    --num-envs 1 \
    --async-datarate 100 \
    --env-id CartPole-v0 \
    --total-timesteps 30_000 \
    --wandb-entity "the-orbital-mind" \
    --wandb-project-name "async-mdp" \
    --track
    
poetry run python src/dqn.py \
    --seed 1 \
    --num-envs 1 \
    --env-id CartPole-v0 \
    --total-timesteps 30_000 \
    --wandb-entity "the-orbital-mind" \
    --wandb-project-name "sync-mdp" \
    --track
"""

# TODO(adrian): send the agent a list of tuples, instead of selecting for the agent.


@dataclass
class Args:
    async_datarate: int = None  # Hz
    """the data rate of the async environment"""
    num_repeat_actions: int = None
    """the number of repeated actions used to be deterministic"""
    accumulate_rewards: bool = True
    """should the environment accumulate rewards for the repeated actions"""
    exp_name: str = os.path.basename(__file__)[: -len(".py")]
    """the name of this experiment"""
    seed: int = 1
    """seed of the experiment"""
    torch_deterministic: bool = True
    """if toggled, `torch.backends.cudnn.deterministic=False`"""
    cuda: bool = True
    """if toggled, cuda will be enabled by default"""
    track: bool = False
    """if toggled, this experiment will be tracked with Weights and Biases"""
    wandb_project_name: str = "cleanRL"
    """the wandb's project name"""
    wandb_entity: str = None
    """the entity (team) of wandb's project"""
    capture_video: bool = False
    """whether to capture videos of the agent performances (check out `videos` folder)"""
    save_model: bool = False
    """whether to save model into the `runs/{run_name}` folder"""
    upload_model: bool = False
    """whether to upload the saved model to huggingface"""
    hf_entity: str = ""
    """the user or org name of the model repository from the Hugging Face Hub"""
    log_frequency: int = 100
    """the frequency of logging"""

    # Algorithm specific arguments
    env_id: str = "CartPole-v1"
    """the id of the environment"""
    total_timesteps: int = 300_000
    """total timesteps of the experiments"""
    learning_rate: float = 0.003
    """the learning rate of the optimizer"""
    num_envs: int = 1
    """the number of parallel game environments"""
    buffer_size: int = 10000
    """the replay memory buffer size"""
    gamma: float = 0.99
    """the discount factor gamma"""
    tau: float = 1.0
    """the target network update rate"""
    target_network_frequency: int = 500
    """the timesteps it takes to update the target network"""
    batch_size: int = 128
    """the batch size of sample from the reply memory"""
    start_e: float = 1
    """the starting epsilon for exploration"""
    end_e: float = 0.05
    """the ending epsilon for exploration"""
    exploration_fraction: float = 0.25
    """the fraction of `total-timesteps` it takes from start-e to go end-e"""
    learning_starts: int = 10000
    """timestep to start learning"""
    train_frequency: int = 10
    """the frequency of training"""

    """
    poetry run python src/dqn.py --num-envs 1 --env-id MountainCar-v0 --total-timesteps 200_000 --wandb-entity the-orbital-mind --wandb-project-name async-mdp-performance-vs-steprate-mountaincar-v0 --track --seed 0 \
    --buffer_size 10_000 \
    --learning_rate 4e-3 \
    --gamma 0.99  \
    --target_network_frequency 600 \
    --batch_size 128 \
    --start_e 1 \
    --end_e 0.07 \
    --exploration_fraction 0.2 \
    --learning_starts 1_000 \
    --train_frequency 16
    1.2e5 = 120,000
    """


def make_env(
    env_id,
    seed,
    idx,
    capture_video,
    run_name,
    async_datarate,
):
    def thunk():
        if capture_video and idx == 0:
            env = gym.make(env_id, render_mode="rgb_array")
            env = gym.wrappers.RecordVideo(env, f"videos/{run_name}")
        else:
            env = gym.make(env_id)
        env = gym.wrappers.RecordEpisodeStatistics(env)
        env.action_space.seed(seed)

        if async_datarate is not None:
            env = AsynchronousGym(
                env,
                environment_steps_per_second=async_datarate,
            )

        return env

    return thunk


# ALGO LOGIC: initialize agent here:
class QNetwork(nn.Module):
    def __init__(self, env):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(np.array(env.single_observation_space.shape).prod(), 120),
            nn.ReLU(),
            nn.Linear(120, 84),
            nn.ReLU(),
            nn.Linear(84, env.single_action_space.n),
        )

    def forward(self, x):
        return self.network(x)


def linear_schedule(start_e: float, end_e: float, duration: int, t: int):
    slope = (end_e - start_e) / duration
    return max(slope * t + start_e, end_e)


if __name__ == "__main__":
    import stable_baselines3 as sb3

    if sb3.__version__ < "2.0":
        raise ValueError(
            """Ongoing migration: run the following command to install the new dependencies:

poetry run pip install "stable_baselines3==2.0.0a1"
"""
        )
    args = tyro.cli(Args)
    assert args.num_envs == 1, "vectorized envs are not supported at the moment"
    run_name = f"{args.env_id}__{args.exp_name}__{args.seed}__{int(time.monotonic())}"
    if args.track:
        import wandb

        wandb.init(
            project=args.wandb_project_name,
            entity=args.wandb_entity,
            sync_tensorboard=True,
            config=vars(args),
            name=run_name,
            monitor_gym=True,
            save_code=True,
        )
    writer = SummaryWriter(f"runs/{run_name}")
    writer.add_text(
        "hyperparameters",
        "|param|value|\n|-|-|\n%s"
        % ("\n".join([f"|{key}|{value}|" for key, value in vars(args).items()])),
    )

    # TRY NOT TO MODIFY: seeding
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.backends.cudnn.deterministic = args.torch_deterministic

    device = torch.device("cuda" if torch.cuda.is_available() and args.cuda else "cpu")

    # env setup
    envs = gym.vector.SyncVectorEnv(
        [
            make_env(
                args.env_id,
                args.seed + i,
                i,
                args.capture_video,
                run_name,
                args.async_datarate,
            )
            for i in range(args.num_envs)
        ]
    )
    assert isinstance(
        envs.single_action_space, gym.spaces.Discrete
    ), "only discrete action space is supported"

    q_network = QNetwork(envs).to(device)
    optimizer = optim.Adam(q_network.parameters(), lr=args.learning_rate)
    target_network = QNetwork(envs).to(device)
    target_network.load_state_dict(q_network.state_dict())

    print("network params ", sum(p.numel() for p in target_network.parameters()))

    rb = ReplayBuffer(
        args.buffer_size,
        envs.single_observation_space,
        envs.single_action_space,
        device,
        handle_timeout_termination=False,
    )

    # TRY NOT TO MODIFY: start the game
    obs, _ = envs.reset(seed=args.seed)

    episodic_return_running_avg = 0
    episodic_return_running_length = 0
    number_of_times_logged = 0
    for agent_step in tqdm(range(args.total_timesteps)):
        start_time = time.monotonic()
        dstart_time = time.monotonic()
        # ALGO LOGIC: put action logic here
        epsilon = linear_schedule(
            args.start_e,
            args.end_e,
            args.exploration_fraction * args.total_timesteps,
            agent_step,
        )
        if random.random() < epsilon:  # or agent_step < args.learning_starts
            actions = np.array(
                [envs.single_action_space.sample() for _ in range(envs.num_envs)]
            )
        else:
            q_values = q_network(torch.Tensor(obs).to(device))
            actions = torch.argmax(q_values, dim=1).cpu().numpy()

        # TRY NOT TO MODIFY: execute the game and log data.
        next_obs, rewards, terminations, truncations, infos = envs.step(actions)

        # TRY NOT TO MODIFY: record rewards for plotting purposes
        if "final_info" in infos:
            for info in infos["final_info"]:
                if info and "episode" in info:
                    writer.add_scalar(
                        "charts/episodic_return", info["episode"]["r"], agent_step
                    )
                    writer.add_scalar(
                        "charts/episodic_length", info["episode"]["l"], agent_step
                    )

        # TRY NOT TO MODIFY: save data to reply buffer; handle `final_observation`
        real_next_obs = next_obs.copy()
        for idx, trunc in enumerate(truncations):
            if trunc:
                real_next_obs[idx] = infos["final_observation"][idx]
        rb.add(obs, real_next_obs, actions, rewards, terminations, infos)

        # TRY NOT TO MODIFY: CRUCIAL step easy to overlook
        obs = next_obs

        # ALGO LOGIC: training.
        if agent_step > args.learning_starts:
            if agent_step % args.train_frequency == 0:
                data = rb.sample(args.batch_size)
                with torch.no_grad():
                    target_max, _ = target_network(data.next_observations).max(dim=1)
                    td_target = data.rewards.flatten() + args.gamma * target_max * (
                        1 - data.dones.flatten()
                    )
                old_val = q_network(data.observations).gather(1, data.actions).squeeze()
                loss = F.mse_loss(td_target, old_val)

                writer.add_scalar("agent_losses/td_loss", loss, agent_step)
                writer.add_scalar(
                    "agent_losses/q_values", old_val.mean().item(), agent_step
                )

                # optimize the model
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # update target network
            if agent_step % args.target_network_frequency == 0:
                writer.add_scalar(
                    "dqn/update_target_network",
                    int(agent_step % args.target_network_frequency == 0),
                    agent_step,
                )
                for target_network_param, q_network_param in zip(
                    target_network.parameters(), q_network.parameters()
                ):
                    target_network_param.data.copy_(
                        args.tau * q_network_param.data
                        + (1.0 - args.tau) * target_network_param.data
                    )

        end_time = time.monotonic()
        sps = agent_step / (end_time - start_time)
        dsps = 1 / (end_time - dstart_time)

        if agent_step % args.log_frequency == 0:
            writer.add_scalar(
                "agent/step_sps",
                dsps,
                agent_step,
            )
            writer.add_scalar(
                "agent/step_dt",
                end_time - dstart_time,
                agent_step,
            )

            if "num_repeat_actions" in infos:
                writer.add_scalar(
                    "environment/num_repeat_actions",
                    infos["num_repeat_actions"],
                    agent_step,
                )

            if "agent_response_time" in infos:
                writer.add_scalar(
                    "environment/agent_response_time",
                    infos["agent_response_time"],
                    agent_step,
                )

            if "ratio" in infos:
                writer.add_scalar(
                    "environment/ratio",
                    infos["ratio"],
                    agent_step,
                )

    if args.save_model:
        model_path = f"runs/{run_name}/{args.exp_name}.cleanrl_model"
        torch.save(q_network.state_dict(), model_path)
        print(f"model saved to {model_path}")
        from src.dqn_eval import evaluate

        episodic_returns = evaluate(
            model_path,
            make_env,
            args.env_id,
            args.async_datarate,
            eval_episodes=100,
            run_name=f"{run_name}-eval",
            Model=QNetwork,
            device=device,
            epsilon=0.05,
        )
        for idx, episodic_return in enumerate(episodic_returns):
            writer.add_scalar("eval/episodic_return", episodic_return, idx)

    envs.close()
    writer.close()
