dimport multiprocessing as mp
import os
import queue
import time

import gymnasium as gym


def getenv_as_int(name, default: int = 0):
    return int(os.getenv(name, str(default)))


class AsyncWrapper:
    def __init__(self, env_name, data_rate=2, worker_queue_size=-1, main_queue_size=-1):
        # Buffer to receive actions
        self.worker_buffer = mp.Queue(maxsize=worker_queue_size)
        print("Worker Buffer Size:", worker_queue_size)

        # Buffer to send observations, rewards, and done flags
        self.main_buffer = mp.Queue(maxsize=main_queue_size)
        print("Main Buffer Size:", main_queue_size)

        # Metrics Data
        self.metrics_per_episode_buffer = mp.Queue()

        self.env = gym.make(env_name)
        self.data_rate = data_rate
        self.worker = Worker(
            worker_buffer=self.worker_buffer,
            main_buffer=self.main_buffer,
            metrics_per_episode_buffer=self.metrics_per_episode_buffer,
            env=self.env,
            data_rate=self.data_rate,
        )

    def start(self):
        self.worker.daemon = True  # Set worker as daemon
        self.worker.start()

    def step(self, action):
        self.worker_buffer.put(action)
        out = self.main_buffer.get()
        return out

    def close(self):
        self.env.close()


class Worker(mp.Process):
    def __init__(
        self, worker_buffer, main_buffer, metrics_per_episode_buffer, env, data_rate=2
    ):
        super(Worker, self).__init__()
        self.worker_buffer = worker_buffer
        self.main_buffer = main_buffer
        self.metrics_per_episode_buffer = metrics_per_episode_buffer
        self.env = env
        self.data_rate = data_rate
        self.running = True
        self._ep = 0

    def run(self):
        observation, info = self.env.reset()
        total_reward = 0
        terminated = truncated = False

        self.main_buffer.put_nowait(
            {
                "observation": observation,
                "reward": 0,
                "terminated": terminated,
                "truncated": truncated,
                "info": info,
            }
        )

        if getenv_as_int("WAIT_FOR_FIRST_ACTION") > 0:
            last_action = self.env.action_space.sample()
        else:
            last_action = self.worker_buffer.get()

        # asynchronous
        while self.running:
            dt = 0
            action = None
            while dt < 1 / self.data_rate:
                start_time = time.monotonic()
                action_to_be = None
                try:
                    action_to_be = self.worker_buffer.get_nowait()
                except:
                    pass

                if action_to_be is not None:
                    action = action_to_be
                else:
                    action = last_action

                end_time = time.monotonic()
                dt += end_time - start_time

            # if action is None:
            #     action = self.env.action_space.sample()
            #     if getenv_as_int("DEBUG") > 0:
            #         print("Random Action:", action)
            # else:
            #     if getenv_as_int("DEBUG") > 0:
            #         print("Action:", action)

            payload = self.env.step(action)
            payload = {
                "observation": payload[0],
                "reward": payload[1],
                "terminated": payload[2],
                "truncated": payload[3],
                "info": payload[4],
            }
            total_reward += payload.get("reward")

            payload["info"].update({"total_reward": total_reward})

            try:
                self.main_buffer.put_nowait(payload)
            except queue.Full:
                if getenv_as_int("DEBUG") > 0:
                    print(
                        "Error:",
                        "Main Buffer Full",
                        f"Dropping {payload}",
                    )
                pass

            if payload.get("terminated"):
                self._ep += 1
                metrics_dic = payload.get("info")
                metrics_dic.update({"episode": self._ep})
                self.metrics_per_episode_buffer.put(metrics_dic)
                print("put in metrics")

                observation, info = self.env.reset()
                terminated = False
                truncated = False
                total_reward = 0
                self.main_buffer.put_nowait(
                    {
                        "observation": observation,
                        "reward": 0,
                        "terminated": terminated,
                        "truncated": truncated,
                        "info": info,
                    }
                )


if __name__ == "__main__":
    with mp.Manager() as manager:
        shared_stack = manager.Stack()

# Example usage
# if __name__ == "__main__":
#     data_rate = 100
#     num_episodes = 10
#     env_wrapper = AsyncWrapper(
#         "CartPole-v1", data_rate=data_rate, worker_queue_size=1, main_queue_size=0
#     )
#     env_wrapper.start()

#     data = []

#     try:
#         while len(data) < num_episodes - 1:
#             observation = env_wrapper.env.reset()
#             terminated = False
#             agent_perspective_total_reward = 0
#             while not terminated:
#                 action = env_wrapper.env.action_space.sample()

#                 # clear old buffer
#                 old_reward = 0
#                 i = 0
#                 while not env_wrapper.main_buffer.empty():
#                     payload = env_wrapper.main_buffer.get()
#                     old_reward += payload.get("reward")
#                     i += 1

#                 payload = env_wrapper.step(action)
#                 agent_perspective_total_reward += payload.get("reward")
#                 if not env_wrapper.metrics_per_episode_buffer.empty():
#                     while not env_wrapper.metrics_per_episode_buffer.empty():
#                         data.append(env_wrapper.metrics_per_episode_buffer.get())
#                     break
#                 print(len(data))
#                 time.sleep(1 / 2)  # simulate agent processing delay

#             print(
#                 "Episode Reward:",
#                 agent_perspective_total_reward,
#                 "Environments perspective total reward:",
#                 payload.get("total_reward", float("nan")),
#             )
#     finally:
#         env_wrapper.close()  # Close the environment when terminated

#     while not env_wrapper.metrics_per_episode_buffer.empty():
#         data.append(env_wrapper.metrics_per_episode_buffer.get())

#     import numpy as np

#     rewards = [d.get("total_reward", 0) for d in data]
#     rewards = np.array(rewards)

#     # Print metrics
#     print(
#         f"""
#           Metrics:
#           Number of episodes: {len(data)}
#           Datarate hyperparameter of environment: 1 / {data_rate}
#           Average return: {rewards.mean():.2f}
#             Std of return: {rewards.std():.2f}
#             Max return: {rewards.max():.2f}
#             Min return: {rewards.min():.2f}
#             95% confidence interval: {np.percentile(rewards, [2.5, 97.5])}
#     """
#     )
