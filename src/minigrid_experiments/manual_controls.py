#!/usr/bin/env python3

import gymnasium as gym
import numpy as np
import torch
from minigrid.minigrid_env import MiniGridEnv
from minigrid.wrappers import RGBImgPartialObsWrapper, ImgObsWrapper

import cv2


def process_key(key, env):
    """Map key presses to actions and interact with the environment."""
    key_to_action = {
        ord("w"): env.actions.forward,  # Move forward
        ord("a"): env.actions.left,  # Turn left
        ord("d"): env.actions.right,  # Turn right
        ord(" "): env.actions.toggle,  # Toggle (interact)
        ord("p"): env.actions.pickup,  # Pickup
        ord("q"): None,  # Quit the game
        27: None,  # Esc key to quit the game
    }

    return key_to_action.get(key, None)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env-id",
        type=str,
        help="gym environment to load",
        choices=gym.envs.registry.keys(),
        default="MiniGrid-MultiRoom-N6-v0",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="random seed to generate the environment with",
        default=None,
    )
    parser.add_argument(
        "--tile-size", type=int, help="size at which to render tiles", default=32
    )
    parser.add_argument(
        "--agent-view",
        action="store_true",
        help="draw the agent sees (partially observable view)",
    )
    parser.add_argument(
        "--agent-view-size",
        type=int,
        default=7,
        help="set the number of grid spaces visible in agent-view ",
    )
    parser.add_argument(
        "--screen-size",
        type=int,
        default="640",
        help="set the resolution for pygame rendering (width and height)",
    )

    args = parser.parse_args()

    env: MiniGridEnv = gym.make(
        args.env_id,
        tile_size=args.tile_size,
        render_mode="human",
        agent_pov=args.agent_view,
        agent_view_size=args.agent_view_size,
    )

    # This now produces an RGB tensor only
    obs, _ = env.reset()

    while True:
        data = obs["image"]

        data = cv2.flip(
            cv2.rotate(
                data,
                # rotate counter clockwise
                cv2.ROTATE_90_COUNTERCLOCKWISE,
            ),
            0,  # flip vertically
        )
        print(data.sum(-1))
        # horizontally flip the image
        cv2.imshow(
            "Observation",
            cv2.resize(data * 51, (256, 256), interpolation=cv2.INTER_NEAREST),
        )

        # Wait for key press
        key = cv2.waitKey(0)

        # Quit if 'q' is pressed
        if key == ord("q") or key == 27:
            break

        # Map the key to an action
        action = process_key(key, env)

        # If a valid action was selected
        if action is not None:
            # Take a step in the environment
            obs, _, done, truncated, _ = env.step(action)

            if done or truncated:
                # Reset the environment if done
                obs, _ = env.reset()
        else:
            print(f"Invalid key: {key}")

    cv2.destroyAllWindows()


# python src/minigrid_experiments/manual_controls.py
# python src/minigrid_experiments/manual_controls.py --agent-view
