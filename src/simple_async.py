import math
import time
from typing import Any, TypeVar
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


class AsyncGymWrapper(gym.Wrapper):
    def __init__(
        self,
        env: gym.Env,
        environment_steps_per_second: int = 2,
        max_steps: int = 300_000,
        repeat_actions: int = None,
        accumulate_rewards: bool = True,
    ):
        """
        Async Wrapper simulates the _asynchronous problem setting_ where the rate
            at which the agent and environment interact is different.
        The environment will have a limited number of timesteps for learning, hence
            we use gymnasium.wrappers.TimeLimit to enforce this.
        We use repeat actions to simulate the asynchronous setting.
        If the agent is slow, the environment will repeat the last action preference
            until the agent is caught up, accumulating rewards, and then play the
            agent's new action preference.
        If the agent is fast, the environment will play the agent's action preference.
        If at any point the episode is terminated or truncated, the environment will
            return immediately with the accumulated reward and episode statistics.
        """
        if environment_steps_per_second is not None:
            self.environment_sps = environment_steps_per_second
        else:
            self.environment_sps = 1
        self._seconds_since_last_action = None
        self._roundtrip_start_time = None
        self._last_action = None
        self.repeat_actions = repeat_actions
        self.accumulate_rewards = accumulate_rewards

        gym.Wrapper.__init__(self, env)

    def reset(self, **kwargs):
        self._roundtrip_start_time = time.monotonic()
        measuring_env_step_start_time = time.monotonic()
        out = self.env.reset(**kwargs)
        self._last_action = self.env.action_space.sample()
        self.measuring_env_step = time.monotonic() - measuring_env_step_start_time
        return out

    def step(
        self,
        action,
    ):
        self._seconds_since_last_action = time.monotonic() - self._roundtrip_start_time

        if self.repeat_actions is None:
            repeated_actions = math.floor(
                self.environment_sps
                * self._seconds_since_last_action
                # self.environment_sps / (1 / self._seconds_since_last_action)
            )
        else:
            repeated_actions = self.repeat_actions

        accumulated_reward = 0
        for i in range(repeated_actions):
            observation, reward, truncated, terminated, info = self.env.step(
                self._last_action
            )
            if self.accumulate_rewards:
                accumulated_reward += reward

            if truncated or terminated:
                info.update(
                    {
                        "repeated_actions": i + 1,
                        "environment_roundtrip_dt": self._seconds_since_last_action,
                    }
                )

                self._roundtrip_start_time = time.monotonic()
                if self.accumulate_rewards:
                    return (
                        observation,
                        accumulated_reward,
                        truncated,
                        terminated,
                        info,
                    )
                else:
                    return (observation, reward, truncated, terminated, info)

        measuring_env_step_start_time = time.monotonic()
        observation, reward, truncated, terminated, info = self.env.step(action)
        self.measuring_env_step = time.monotonic() - measuring_env_step_start_time
        self._last_action = action

        info.update(
            {
                "repeated_actions": repeated_actions,
                "environment_roundtrip_dt": self._seconds_since_last_action,
            }
        )
        self._roundtrip_start_time = time.monotonic()

        if self.accumulate_rewards:
            return (
                observation,
                reward + accumulated_reward,
                truncated,
                terminated,
                info,
            )
        else:
            return (observation, reward, truncated, terminated, info)


if __name__ == "__main__":

    # Pytests using mountaincar, we can sample the action space for the agent, and verify the asyncwrapper by looking at the accumulated rewareds.
    # if the environment's datarate was 1 step per second, and the agent took 0.0 seconds, the environment should repeat 0 actions and return the agent's action preference. 1 data packet should come back.
    # if the environment's datarate was 1 step per second, and the agent took 0.5 seconds, the environment should repeat 0 actions and return the agent's action preference. 1 data packet should come back.
    # if the environment's datarate was 1 step per second, and the agent took 0.9 seconds, the environment should repeat 0 actions and return the agent's action preference. 1 data packet should come back.

    # If the environment's datarate was 1 step per second, and the agent took 1 second, the environment should repeat 1 action, and return the action's action preference, meaning 2 data packets should come back.
    # If the environment's datarate was 1 step per second, and the agent took 1.1 second, the environment should repeat 1 action, and return the action's action preference, meaning 2 data packets should come back.
    # If the environment's datarate was 1 step per second, and the agent took 1.9 second, the environment should repeat 1 action, and return the action's action preference, meaning 2 data packets should come back.
    # If the environment's datarate was 1 step per second, and the agent took 2 second, the environment should repeat 2 action, and return the action's action preference, meaning 3 data packets should come back.

    # If the environment's datarate was 10 steps per second, and the agent took 1/10 second, the environment should repeat 1 action, and return the action's action preference, meaning 2 data packets should come back.

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
    env = AsyncGymWrapper(env, environment_steps_per_second=1, max_steps=10)

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
        env.environment_steps_per_second = environment_rate
        observation = env.reset()
        action = agent_decide_action(agent_rate)
        observation, reward, truncated, terminated, info = env.step(action)
        # the first time is always instintanious
        assert reward == -1, f"expected -1 but got {reward}"
        assert (
            info.get("repeated_actions") == 0
        ), f"expected 0 but got {info.get('repeated_actions')}"

        # the second time is when we can get delays
        action = agent_decide_action(agent_rate)
        observation, reward, truncated, terminated, info = env.step(action)
        assert reward == expected_reward, f"expected {expected_reward} but got {reward}"
        assert expected_repeat_actions == info.get(
            "repeated_actions"
        ), f"expected {expected_repeat_actions} but got {info.get('repeated_actions')}"

    # check if the environment is enforcing the max_steps
    env = gym.make("MountainCar-v0")
    env = AsyncGymWrapper(env, environment_steps_per_second=1, max_steps=10)
    env.environment_steps_per_second = 1
    observation = env.reset()
    i = 0
    while True:
        action = agent_decide_action(0)
        observation, reward, truncated, terminated, info = env.step(action)
        i += 1
        if truncated or terminated:
            env.reset()
            break

    assert i == 10, f"expected 10 but got {i}"
