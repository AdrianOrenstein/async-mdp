from minigrid.core.actions import Actions
from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import Ball, Goal, Key, Wall
from minigrid.minigrid_env import MiniGridEnv
from src.minigrid_experiments.maze import create_maze


class LargeEmpty(MiniGridEnv):
    def __init__(
        self,
        size=32,
        agent_start_pos=None,
        agent_start_dir=0,
        max_steps: int | None = None,
        **kwargs,
    ):
        if agent_start_pos is not None:
            self.agent_start_pos = agent_start_pos
        else:
            self.agent_start_pos = (1, size // 2)
        self.agent_start_dir = agent_start_dir

        mission_space = MissionSpace(mission_func=self._gen_mission)

        if max_steps is None:
            max_steps = size**2

        super().__init__(
            mission_space=mission_space,
            grid_size=size,
            # Set this to True for maximum speed
            see_through_walls=True,
            max_steps=max_steps,
            **kwargs,
        )

    @staticmethod
    def _gen_mission():
        return "hello world"

    def _gen_grid(self, width, height):
        # Create an empty grid
        self.grid = Grid(width, height)

        # Generate the surrounding walls
        self.grid.wall_rect(0, 0, width, height)

        # Place a goal square in the bottom-right corner
        self.put_obj(Goal(), width - 2, height // 2)

        # Place the agent
        if self.agent_start_pos is not None:
            self.agent_pos = self.agent_start_pos
            self.agent_dir = self.agent_start_dir
        else:
            self.place_agent()

        self.mission = "find the green goal"


class Maze(MiniGridEnv):
    def __init__(
        self,
        size=15,
        agent_start_dir=0,
        max_steps: int | None = None,
        **kwargs,
    ):
        self.agent_start_pos = (1, 1)
        self.agent_start_dir = agent_start_dir

        mission_space = MissionSpace(mission_func=self._gen_mission)

        if max_steps is None:
            max_steps = size**2

        super().__init__(
            mission_space=mission_space,
            grid_size=size,
            # Set this to True for maximum speed
            see_through_walls=True,
            max_steps=max_steps,
            **kwargs,
        )

    @staticmethod
    def _gen_mission():
        return "hello world"

    def _gen_grid(self, width, height):
        # Create an empty grid
        self.grid = Grid(width, height)

        # Generate the Maze
        maze_data = create_maze(width // 2, height // 2)
        print(maze_data.shape)

        print(maze_data)

        for x, row in enumerate(maze_data):
            for y, cell in enumerate(row):
                if cell == 1:
                    self.grid.set(x, y, Wall())
                else:
                    self.grid.set(x, y, None)

        # Place the player
        if self.agent_start_pos is not None:
            self.agent_pos = self.agent_start_pos
            self.agent_dir = self.agent_start_dir
        else:
            self.place_agent()

        # Place the goal square
        self.put_obj(Goal(), width - 2, height - 2)

        self.mission = "navigate the maze and get to the goal"
