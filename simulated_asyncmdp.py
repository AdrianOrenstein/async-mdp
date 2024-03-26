


if __name__ == "__main__":

    # given an environment datarate and agent datarate, print whenever the agent sends data by the right time
    agent_rate = 1  # hz
    env_rate = 1  # hz
    dt = 0
    # need to simulate sending and receiving data, we can also test the push pop behaviour here.
    env_counter = 0
    agent_counter = 0
    while True:
        dt += 1 / env_rate

        # use modolo to check if the agent should send data
        if dt % (1 / agent_rate) == 0:
            agent_counter += 1

        if dt % (1 / env_rate) == 0:
            env_counter += 1

        print(f"Agent counter: {agent_counter}, Environment counter: {env_counter}")
