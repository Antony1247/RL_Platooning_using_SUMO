import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from PlatooningEnv import PlatooningParallelEnv
from agent import QNetwork


def train_dqn(env, agents, episodes, start_epsilon=1.0, end_epsilon=0.01, decay_rate=0.995):
    optimizers = {agent: optim.Adam(agents[agent].parameters(), lr=0.01) for agent in env.agents}
    epsilon = start_epsilon

    for episode in range(episodes):
        state = env.reset()
        done = {agent: False for agent in env.agents}
        total_rewards = {agent: 0 for agent in env.agents}

        while not all(done.values()):
            actions = {}
            step_rewards={}
            for agent in env.agents:
                if np.random.rand() < epsilon:
                    # Take random action
                    action = env.action_spaces[agent].sample()
                else:
                    # Take the action with the highest Q-value
                    state_tensor = torch.from_numpy(state[agent]).float().unsqueeze(0)
                    q_values = agents[agent](state_tensor)
                    action = torch.argmax(q_values).item()

                actions[agent] = action

            next_state, rewards, done, _ = env.step(actions)

            for agent in env.agents:
                print(f"  Agent: {agent}, Action: {actions[agent]}, Reward: {rewards[agent]}")
                step_rewards[agent] = rewards[agent]


            for agent in env.agents:
                reward = rewards[agent]
                total_rewards[agent] += reward
                next_state_tensor = torch.from_numpy(next_state[agent]).float().unsqueeze(0)
                state_tensor = torch.from_numpy(state[agent]).float().unsqueeze(0)

                current_q_values = agents[agent](state_tensor)
                next_q_values = agents[agent](next_state_tensor)

                max_next_q = torch.max(next_q_values)
                target_q_value = reward + 0.99 * max_next_q * (1 - int(done[agent]))

                loss = F.mse_loss(current_q_values.squeeze(0)[actions[agent]], target_q_value)
                optimizers[agent].zero_grad()
                loss.backward()
                optimizers[agent].step()

            state = next_state

        # Decay epsilon
        epsilon = max(end_epsilon, epsilon * decay_rate)
        print(f'Episode {episode + 1}: Total Rewards: {total_rewards}, Epsilon: {epsilon}')




if __name__ == "__main__":
    env = PlatooningParallelEnv()
    agents = {agent: QNetwork(env.observation_spaces[agent].shape[0], env.action_spaces[agent].n) for agent in env.agents}

    # Train the agents
    train_dqn(env, agents, episodes=10)