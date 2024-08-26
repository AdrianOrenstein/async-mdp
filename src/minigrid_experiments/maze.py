# From https://medium.com/@msgold/using-python-to-create-and-solve-mazes-672285723c96

import matplotlib.pyplot as plt
import numpy as np
import random
from queue import Queue
import matplotlib.animation as animation


def create_maze(width, height):
    # Create a grid filled with walls
    maze = np.ones((width * 2 + 1, height * 2 + 1), dtype=int)

    # Define the starting point
    x, y = (1, 1)
    maze[2 * x, 2 * y] = 0

    # Initialize the stack with the starting point
    stack = [(x, y)]
    while len(stack) > 0:
        x, y = stack[-1]

        # Define possible directions
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (
                nx >= 0
                and ny >= 0
                and nx < width
                and ny < height
                and maze[2 * nx + 1, 2 * ny + 1] == 1
            ):
                maze[2 * nx + 1, 2 * ny + 1] = 0
                maze[2 * x + 1 + dx, 2 * y + 1 + dy] = 0
                stack.append((nx, ny))
                break
        else:
            stack.pop()

    # Create an entrance and an exit
    maze[1, 1] = 0
    maze[-2, -2] = 0

    return maze


def find_path(maze):
    # BFS algorithm to find the shortest path
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    start = (1, 1)
    end = (maze.shape[0] - 2, maze.shape[1] - 2)
    visited = np.zeros_like(maze, dtype=bool)
    visited[start] = True
    queue = Queue()
    queue.put((start, []))
    while not queue.empty():
        (node, path) = queue.get()
        for dx, dy in directions:
            next_node = (node[0] + dx, node[1] + dy)
            if next_node == end:
                return path + [next_node]
            if (
                next_node[0] >= 0
                and next_node[1] >= 0
                and next_node[0] < maze.shape[0]
                and next_node[1] < maze.shape[1]
                and maze[next_node] == 0
                and not visited[next_node]
            ):
                visited[next_node] = True
                queue.put((next_node, path + [next_node]))


def draw_maze(maze, path=None):
    fig, ax = plt.subplots(figsize=(10, 10))

    # Set the border color to white
    fig.patch.set_edgecolor("white")
    fig.patch.set_linewidth(0)

    ax.imshow(maze, cmap=plt.cm.binary, interpolation="nearest")

    # Draw the solution path if it exists
    if path is not None:
        x_coords = [x[1] for x in path]
        y_coords = [y[0] for y in path]
        ax.plot(x_coords, y_coords, color="red", linewidth=2)

    ax.set_xticks([])
    ax.set_yticks([])

    # Draw entry and exit arrows
    ax.arrow(0.5, 1, 0.4, 0, fc="green", ec="green", head_width=0.3, head_length=0.3)
    ax.arrow(
        maze.shape[1] - 2,
        maze.shape[0] - 2,
        0.4,
        0,
        fc="blue",
        ec="cyan",
        head_width=0.3,
        head_length=0.3,
    )

    plt.show()


def draw_maze_animated(maze, path=None):
    fig, ax = plt.subplots(figsize=(10, 10))

    # Set the border color to white
    fig.patch.set_edgecolor("white")
    fig.patch.set_linewidth(0)

    ax.imshow(maze, cmap=plt.cm.binary, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])

    # Prepare for path animation
    if path is not None:
        (line,) = ax.plot([], [], color="red", linewidth=2)

        def init():
            line.set_data([], [])
            return (line,)

        # update is called for each path point in the maze
        def update(frame):
            x, y = path[frame]
            line.set_data(
                *zip(*[(p[1], p[0]) for p in path[: frame + 1]])
            )  # update the data
            return (line,)

        ani = animation.FuncAnimation(
            fig,
            update,
            frames=range(len(path)),
            init_func=init,
            blit=True,
            repeat=False,
            interval=20,
        )

    # Draw entry and exit arrows
    ax.arrow(0.5, 1, 0.4, 0, fc="green", ec="green", head_width=0.3, head_length=0.3)
    ax.arrow(
        maze.shape[1] - 2,
        maze.shape[0] - 2,
        0.4,
        0,
        fc="blue",
        ec="cyan",
        head_width=0.3,
        head_length=0.3,
    )

    plt.show()


if __name__ == "__main__":
    dim = int(input("Enter the dimension of the maze: "))
    maze = create_maze(dim, dim + 5)
    path = find_path(maze)
    draw_maze_animated(maze, path)

# python src/minigrid_experiments/maze.py
