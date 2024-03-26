import multiprocessing as mp
import queue
import time
from typing import Any, List
import gymnasium as gym
import os
from multiprocessing import Process, Manager


def get_env_as_int(name, default: int = 0):
    return int(os.getenv(name, str(default)))


@staticmethod
def queue_get(l: List):
    return l.pop(0)


@staticmethod
def queue_put(l: List, item: Any):
    return l.append(item)


@staticmethod
def stack_get(l: List):
    return l.pop()


@staticmethod
def stack_put(l: List, item: Any):
    return l.append(item)


class AsyncWrapper:
    def __init__(
        self,
        env: gym,
        data_rate=2,
        agent_send_fn=stack_put,
        agent_receive_fn=stack_get,
        env_send_fn=queue_put,
        env_receive_fn=queue_get,
    ):
        manager = Manager()

        # Environment
        self._env_buffer = manager.list()
        self._env_send = lambda payload: env_send_fn(self._env_buffer, payload)
        self._env_receive = lambda: env_receive_fn(self._env_buffer)

        # Agent
        self._agent_buffer = manager.list()
        self._agent_send = lambda payload: agent_send_fn(self._agent_buffer, payload)
        self._agent_receive = lambda: agent_receive_fn(self._agent_buffer)

        self._data_rate = data_rate
        self._env = env

        self.worker = EnvironmentWorker(
            environment_buffer=self._env_buffer,
            agent_buffer=self._agent_buffer,
            env=self._env,
            data_rate=self._data_rate,
        )

        self.start()

    def reset(self):
        out = self._env.reset()
        self.worker._timestep = 0
        return out

    def start(self):
        # Set worker as daemon so that it gracefully exits if the main process is terminated
        self.worker.daemon = True
        self.worker.start()

    def step(self, action):
        self._agent_send(action)
        return self._agent_receive()

    def close(self):
        self._env.close()


class EnvironmentWorker(mp.Process):
    def __init__(
        self,
        environment_buffer: List,
        agent_buffer: List,
        env: gym,
        data_rate: int = 2,
    ):
        super(EnvironmentWorker, self).__init__()
        self._env_buffer = environment_buffer
        self._agent_buffer = agent_buffer
        self._env = env
        self._data_rate = data_rate

    def run(self):
        self._timestep = 0
        self.running = True

        observation, info = self._env.reset()
        terminated = truncated = False

        info.update({"timestep": self._timestep})

        self._env_buffer.append(
            {
                "observation": observation,
                "reward": 0,
                "terminated": terminated,
                "truncated": truncated,
                "info": info,
            }
        )

        # wait for action in buffer
        while len(self._env_buffer) == 0:
            pass

        while self.running:
            print(f"self._env_buffer: {self._env_buffer}")
            action = self._env_buffer.pop()

            print(action)
            self.running = False
            break

        # if get_env_as_int("WAIT_FOR_FIRST_ACTION") > 0:
        #     last_action = self._env.action_space.sample()
        # else:
        #     while len(self._env_buffer) == 0:
        #         pass
        #     last_action = self._env_buffer.pop(0)

        # total_reward = 0
        # step_rate_of_agent = 2
        # dt = 0

        # while self.running:
        #     action_to_be = self._env_buffer.pop(0)
        #     dt += 1 / step_rate_of_agent

        #     payload = self._env.step(action)
        #     payload = {
        #         "observation": payload[0],
        #         "reward": payload[1],
        #         "terminated": payload[2],
        #         "truncated": payload[3],
        #         "info": payload[4],
        #     }

        #     total_reward += payload.get("reward")
        #     payload["info"].update(
        #         {"total_reward": total_reward, "timestep": self._timestep}
        #     )

        #     self._agent_buffer.put(payload)

        #     self._timestep += 1


# Example usage
if __name__ == "__main__":
    data_rate = 100
    num_timestepisodes = 10
    env_wrapper = AsyncWrapper(
        gym.make("CartPole-v1"),
        data_rate=2,
    )

    data = []

    try:
        while len(data) < num_timestepisodes - 1:

            terminated = False
            agent_perspective_total_reward = 0
            while not terminated:

                # wait for data
                while len(env_wrapper._agent_buffer) == 0:
                    pass

                # clear data, and get last
                old_reward = 0
                i = 0
                while len(env_wrapper._agent_buffer) > 0:
                    payload = env_wrapper._agent_buffer.pop()
                    old_reward += payload.get("reward")
                    i += 1

                action = env_wrapper._env.action_space.sample()

                payload = env_wrapper.step(action)
                agent_perspective_total_reward += payload.get("reward")

                while len(env_wrapper._evaluation_buffer) > 0:
                    data.append(env_wrapper._evaluation_buffer.get())

                time.sleep(1 / 2)
                break

            print(
                "Episode Reward:",
                agent_perspective_total_reward,
                "_environments perspective total reward:",
                payload.get("total_reward", float("nan")),
            )
            break
    finally:
        env_wrapper.close()  # Close the _environment when terminated

    while not env_wrapper._evalutation_buffer.empty():
        data.append(env_wrapper._evalutation_buffer.get())

    import numpy as np

    rewards = [d.get("total_reward", 0) for d in data]
    rewards = np.array(rewards)

    # Print metrics
    print(
        f"""
          Metrics:
          Number of episodes: {len(data)}
          Datarate hyperparameter of _environment: 1 / {data_rate}
          Average return: {rewards.mean():.2f}
            Std of return: {rewards.std():.2f}
            Max return: {rewards.max():.2f}
            Min return: {rewards.min():.2f}
            95% confidence interval: {np.percentile(rewards, [2.5, 97.5])}
    """
    )


# Test that the _environment has queue like access behaviour with pytest
# Test that the agent has stack like access behaviour with pytest
