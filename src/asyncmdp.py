import os
import time
from multiprocessing import Manager, Process
from loguru import logger
import gymnasium as gym


# Define send and receive functions as standalone, top-level functions
def queue_get(l):
    return l.pop(0)


def queue_put(l, item):
    l.append(item)


def stack_get(l):
    return l.pop()


def stack_put(l, item):
    l.append(item)


# Helper function to convert environment variables to integers
def get_env_as_int(name, default: int = 0):
    return int(os.getenv(name, str(default)))


import gym
from multiprocessing import Manager
from gym import spaces


class AsyncGymWrapper(gym.Wrapper):
    def __init__(
        self,
        env,
        data_rate=2,
        agent_send_fn=stack_put,
        agent_receive_fn=stack_get,
        env_send_fn=queue_put,
        env_receive_fn=queue_get,
    ):
        super().__init__(env)
        manager = Manager()

        # Initialize buffers
        self._env_buffer = manager.list()
        self._agent_buffer = manager.list()

        # Assign functions
        self._agent_send = lambda payload: agent_send_fn(self._env_buffer, payload)
        self._agent_receive = lambda: agent_receive_fn(self._agent_buffer)

        self._data_rate = data_rate

        self.worker = EnvironmentWorker(
            environment_buffer=self._env_buffer,
            agent_buffer=self._agent_buffer,
            env=self.env,
            data_rate=self._data_rate,
            env_send_fn=env_send_fn,
            env_receive_fn=env_receive_fn,
        )

        self.start()

    def reset(self, **kwargs):
        out = super().reset(**kwargs)  # Reset the underlying env
        self.worker._timestep = 0
        return out

    def start(self):
        # Set worker as daemon
        self.worker.daemon = True
        self.worker.start()

    def step(self, action):
        self._agent_send(action)

        # agent waits for data
        while len(self._agent_buffer) == 0:
            pass

        return self._agent_receive().values()

    def close(self):
        self.worker.terminate()
        self.worker.running = False
        time.sleep(0.1)
        try:
            self.worker.close()
        except Exception as e:
            logger.error(f"Error closing environment worker: {e}")
            pass
        del self.worker
        super().close()  # Make sure to close the underlying env as well


class EnvironmentWorker(Process):
    def __init__(
        self,
        environment_buffer,
        agent_buffer,
        env: gym.Env,
        data_rate: int = 2,
        env_send_fn=queue_put,
        env_receive_fn=queue_get,
    ):
        super(EnvironmentWorker, self).__init__()
        self._env_buffer = environment_buffer
        self._agent_buffer = agent_buffer
        self._env = env
        self._env_send_fn = env_send_fn
        self._env_receive_fn = env_receive_fn
        self._data_rate = data_rate

    def _env_send(self, payload):
        self._env_send_fn(self._agent_buffer, payload)

    def _env_receive(self):
        return self._env_receive_fn(self._env_buffer)

    def run(self):
        self._timestep = 0
        self._global_timestep = 0
        self._episodic_return = 0
        self.running = True

        self._logging_data = []

        observation, info = self._env.reset()
        terminated = truncated = False

        info.update({"timestep": self._timestep})

        if get_env_as_int("DEBUG") > 0:
            print("Environment sending data")
        self._env_send(
            {
                "observation": observation,
                "reward": 0,
                "terminated": terminated,
                "truncated": truncated,
                "info": info,
            },
        )
        if get_env_as_int("DEBUG") > 0:
            print("Environment sent data")

        # Process loop
        while self.running:
            start_time = time.monotonic()

            if self._data_rate == 0:
                while len(self._env_buffer) == 0:
                    _ = time.monotonic() - start_time
                    continue
                action = self._env_receive()

            else:
                action = self._env.action_space.sample()

                while (time.monotonic() - start_time) < (1 / self._data_rate):
                    if len(self._env_buffer) == 0:
                        continue
                    else:
                        action = self._env_receive()

            if get_env_as_int("DEBUG") > 0:
                print("Environment received action")

            observation, reward, terminated, truncated, info = self._env.step(action)
            self._logging_data.append(
                {
                    "timestep": self._timestep,
                    "reward": reward,
                }
            )
            self._timestep += 1
            self._episodic_return += reward

            info.update(
                {
                    "timestep": self._timestep,
                    "my_episodic_return": self._episodic_return,
                }
            )

            if terminated or truncated:
                self._global_timestep += self._timestep
                info.update(
                    {
                        "logging_data": self._logging_data,
                        "global_environment_time": self._global_timestep,
                    }
                )

            payload = {
                "observation": observation,
                "reward": reward,
                "terminated": terminated,
                "truncated": truncated,
                "info": info,
            }

            self._env_send(payload)

            if terminated or truncated:
                self._episodic_return = 0
                self._timestep = 0
                observation, info = self._env.reset()
                terminated = False
                truncated = False

                info.update(
                    {
                        "timestep": self._timestep,
                        "my_episodic_return": self._episodic_return,
                    }
                )
                self._env_send(
                    {
                        "observation": observation,
                        "reward": 0,
                        "terminated": terminated,
                        "truncated": truncated,
                        "info": info,
                    }
                )

                self._logging_data = []

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
    env_wrapper = AsyncGymWrapper(
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
                if get_env_as_int("DEBUG") > 0:
                    print("Agent waiting for data")

                while len(env_wrapper._agent_buffer) == 0:
                    pass

                if get_env_as_int("DEBUG") > 0:
                    print("Agent received data")

                if get_env_as_int("DEBUG") > 0:
                    print("Agent deciding action")

                action = env_wrapper._env.action_space.sample()

                if get_env_as_int("DEBUG") > 0:
                    print("Agent sending action")

                observation, reward, terminated, truncated, info = env_wrapper.step(
                    action
                )

                if get_env_as_int("DEBUG") > 0:
                    print("Agent received reward, should be learning here")

                data += [reward]

                if get_env_as_int("DEBUG") > 0:
                    print("Agent done learning.")
    finally:
        env_wrapper.close()  # Close the environment when terminated

    import numpy as np

    rewards = np.array(data)

    # Print metrics
    print(
        f"""
          Metrics:
          Number of episodes: {len(data)}
          Datarate hyperparameter of environment: 1 / {data_rate}
          Average return: {rewards.mean():.2f}
            Std of return: {rewards.std():.2f}
            Max return: {rewards.max():.2f}
            Min return: {rewards.min():.2f}
            95% confidence interval: {np.percentile(rewards, [2.5, 97.5])}
    """
    )


# Test that the _environment has queue like access behaviour with pytest
# Test that the agent has stack like access behaviour with pytest
