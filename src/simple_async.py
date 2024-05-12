import math
import time
from typing import Any, Dict, List, Tuple, TypeVar
import gymnasium as gym

ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")

# environment has a limited number of steps: gymnasium.wrappers.TimeLimit(env: Env, max_episode_steps: int)
# environmen will repeat actions if agent is slow by measuring the delta time between when an observation
#   was sent to the agent, and when an action was received. If the agent is faster than the environment the
#   environment will play the agent's action preference, if the agent is slower than the environment then the
#   environment will repeat the old action preference until the agent is caught up, then the agent's new action
#   preference will be played.
# async wrapper applies a time limit, and the action repeat using deltatime, to simulate the asynchronous setting.

# class AsyncGymWrapperWithRepeats(gym.Wrapper):
#     def __init__(self, env: gym.Env):
#         gym.Wrapper.__init__(self, env)

#     def step(self, action: ActType) -> Tuple[List[ObsType], List[float], bool, bool, List[Dict[str, Any]]]:


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
            num_repeat_actions = math.floor(
                self._environment_steps_per_second * agent_response_time
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

    def agent_decide_action(decision_rate):
        agent_start_time = time.monotonic()
        action = env.action_space.sample()
        # compute remaining time from steps per second and sleep that amount
        if decision_rate > 0:
            time.sleep(
                max(0, (1 / decision_rate) - (time.monotonic() - agent_start_time))
            )
        return action

    env = gym.make("MountainCar-v0")
    env = AsynchronousGym(env, environment_steps_per_second=1)

    tests = [
        # equal speed
        (1, 1, -2, 1),
        # agent is faster
        (1, 1 / 2, -1, 0),
        (2, 1, -1, 0),
        (3, 1, -1, 0),
        (4, 1, -1, 0),
        (5, 1, -1, 0),
        # agent is slower
        (1, 2, -3, 2),
        (1, 3, -4, 3),
        (1, 4, -5, 4),
        (1, 5, -6, 5),
    ]

    for agent_rate, environment_rate, expected_reward, expected_repeat_actions in tests:
        (observation, info) = env.reset(environment_steps_per_second=environment_rate)
        assert (
            info.get("num_repeated_actions") == 0
        ), f"expected 0 but got {info.get('num_repeated_actions')}"
        assert env._environment_steps_per_second == environment_rate
        action = agent_decide_action(agent_rate)
        (observations, rewards, truncated, terminated, infos) = env.step(action)

        # just take the last
        observation = observations[-1]
        reward = sum(rewards)
        info = infos[-1]

        # the first time is always instintanious
        assert reward == -1, f"expected {expected_reward} but got {rewards[0]}"

        # the second time is when we can get delays
        action = agent_decide_action(agent_rate)
        observations, rewards, truncated, terminated, infos = env.step(action)

        # just take the last
        observation = observations[-1]
        reward = sum(rewards)
        info = infos[-1]

        assert reward == expected_reward, f"expected {expected_reward} but got {reward}"
