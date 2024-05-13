import math
import time
from typing import Any, Dict, List, Tuple, TypeVar
import gymnasium as gym

ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")

# class AsyncGymWrapperWithRepeats(gym.Wrapper):
#     def __init__(self, env: gym.Env):
#         gym.Wrapper.__init__(self, env)

#     def step(self, action: ActType) -> Tuple[List[ObsType], List[float], bool, bool, List[Dict[str, Any]]]:


def compute_num_repeated_actions(
    environment_steps_per_second: int, agent_response_time: float
) -> int:
    ratio = environment_steps_per_second * agent_response_time
    print(
        f"ratio: {ratio} agent_response_time: {agent_response_time} environment_steps_per_second: {environment_steps_per_second}"
    )
    # If you're on the same rate, you made it.
    rounded_ratio = round(ratio)
    if math.isclose(ratio, rounded_ratio, rel_tol=0.001):
        return max(0, rounded_ratio - 1)

    return max(0, math.floor(ratio))


class AsynchronousGym(gym.Wrapper):
    def __init__(self, env: gym.Env, environment_steps_per_second: int = 2):
        """
        Async Wrapper simulates the _asynchronous problem setting_ where the rate
            at which the agent and environment interact is different.
        The environment will repeat actions if the agent is slow by measuring the
            delta time between when an observation was sent to the agent, and when
            an action was received.
        If the agent is fast, the environment will play the agent's action preference.
        If at any point the episode is terminated or truncated, the environment will
            return immediately with the accumulated reward and episode statistics.
        """
        super(AsynchronousGym, self).__init__(env)
        self._environment_steps_per_second = environment_steps_per_second

        self._seconds_since_last_action = None
        self._roundtrip_start_time = None
        self._last_action = None

    def reset(
        self, environment_steps_per_second: int = None, **kwargs
    ) -> Tuple[ObsType, dict]:
        self._roundtrip_start_time = None
        self._last_action = None
        if environment_steps_per_second is not None:
            self._environment_steps_per_second = environment_steps_per_second

        observation, info = self.env.reset(**kwargs)
        info.update(
            {
                "num_repeated_actions": 0,
                "agent_response_time": 0,
            }
        )
        return (observation, info)

    def step(
        self,
        action,
    ):
        # If the agent is delayed, the environment will repeat the last seen action.
        if self._roundtrip_start_time is None:
            agent_response_time = 0
            num_repeat_actions = 0
        else:
            agent_response_time = time.monotonic() - self._roundtrip_start_time
            num_repeat_actions = compute_num_repeated_actions(
                self._environment_steps_per_second, agent_response_time
            )

        observations = []
        rewards = []
        infos = []
        for i in range(num_repeat_actions):
            observation, reward, truncated, terminated, info = self.env.step(action)
            observations.append(observation)
            rewards.append(reward)
            info.update(
                {
                    "num_repeat_actions": i + 1,
                    "agent_response_time": agent_response_time,
                }
            )
            infos.append(info)

            if terminated or truncated:
                self._roundtrip_start_time = time.monotonic()
                return (observations, rewards, truncated, terminated, infos)

        # Once the environment is caught up, the agent's new action will be played.
        observation, reward, truncated, terminated, info = self.env.step(action)
        observations.append(observation)
        rewards.append(reward)
        info.update(
            {
                "num_repeat_actions": num_repeat_actions,
                "agent_response_time": agent_response_time,
            }
        )
        infos.append(info)
        self._last_action = action

        # Start measuring the agent's response time.
        self._roundtrip_start_time = time.monotonic()
        return (observations, rewards, truncated, terminated, infos)


# class AsynchronousGymWithAccumulateRewardsAndPickLastObs(AsynchronousGym):
#     def __init__(self, env: gym.Env, environment_steps_per_second: int):
#         super(AsynchronousGymWithAccumulateRewardsAndPickLastObs, self).__init__(
#             env, environment_steps_per_second
#         )

#     def step(self, action: ActType) -> Tuple[ObsType, float, bool, Dict[str, Any]]:
#         observations, rewards, truncated, terminated, info = self.step(action)
#         return observations[-1], sum(rewards), truncated, terminated, info


if __name__ == "__main__":
    env = gym.make("MountainCar-v0")
    env = AsynchronousGym(env, environment_steps_per_second=1)

    tests = [
        # agent is slower, bad.
        (1, 2, 1),
        (1, 3, 2),
        (1, 4, 3),
        (1, 5, 4),
        # equal speed, the agent is not delayed, and used the maximum amount of time. great.
        (1, 1, 0),
        (2, 2, 0),
        (5, 5, 0),
        (100, 100, 0),
        (10_000, 10_000, 0),
        # agent is faster. great.
        (1, 0.01, 0),
        (1, 0.25, 0),
        (1, 0.5, 0),
        (1, 0.75, 0),
        (2, 1, 0),
        (3, 1, 0),
        (4, 1, 0),
        (5, 1, 0),
        (10, 1, 0),
        (100, 1, 0),
        (1_000, 1, 0),
        (10_000, 1, 0),
    ]

    # Testing just the logic
    print("Running unit tests")
    for agent_rate, environment_rate, expected_repeat_actions in tests:
        print(
            f"Running test with agent_rate={agent_rate} and environment_rate={environment_rate}"
        )
        num_repeated_actions = compute_num_repeated_actions(
            environment_rate, 1 / agent_rate
        )
        assert (
            num_repeated_actions == expected_repeat_actions
        ), f"A{agent_rate}:E{environment_rate} expected {expected_repeat_actions} but got {num_repeated_actions}"
