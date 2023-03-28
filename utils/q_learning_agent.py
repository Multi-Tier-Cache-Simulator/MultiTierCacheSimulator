import random
import time

import numpy as np


class QLearningAgent:
    def __init__(self, num_states: int, num_actions: int, learning_rate: float, discount_factor: float, epsilon: float):
        self.action_space = range(-num_actions, num_actions)
        print("action_space = %s" % self.action_space)
        self.num_states = num_states
        # Initialize the Q-table with zeros
        self.q_table = np.zeros([self.num_states, len(self.action_space)])
        # Set the hyper_parameters
        self.learning_rate = learning_rate  # learning_rate = 0.1
        self.discount_factor = discount_factor  # discount_factor = 0.99
        # Define the epsilon-greedy exploration strategy
        self.epsilon = epsilon  # epsilon = 0.1
        self.epsilon_decay_value = 0.001
        self.rewards = []

    def get_next_state(self, current_p: int, current_t1_len: int, current_b1_len: int, current_b2_len: int,
                       hit: str):
        # Choose an action using epsilon-greedy exploration
        if random.random() < self.epsilon:
            action = np.random.choice(self.action_space)
            # print("action is random %s" % action)
        else:
            action = np.argmax(self.q_table[current_p]) - self.num_states
            # print("action is argmax %s" % action)

        # if self.epsilon > 0.1:
        #     self.epsilon -= self.epsilon_decay_value
        #     print("new epsilon = %s" % self.epsilon)

        # get next state
        if current_p + action < 0:
            new_state = 0
            # print("new state is %s" % new_state)
        elif current_p + action >= self.num_states:
            new_state = self.num_states - 1
            # print("new state is %s" % new_state)
        else:
            new_state = current_p + action
            # print("new state is %s" % new_state)

        # get the reward
        if hit.__eq__("t1"):
            reward = 100
        elif hit.__eq__("t2"):
            reward = 100
        elif hit.__eq__("b1"):
            if current_b1_len < current_b2_len:
                reward = -10
            else:
                reward = -1
        elif hit.__eq__("b2"):
            if current_b1_len > current_b2_len:
                reward = -10
            else:
                reward = -1
        elif hit.__eq__("Miss"):
            reward = -100
        else:
            reward = 0
        # print("reward is %s" % reward)

        self.rewards.append(reward)
        # update the Q_value
        self.q_table[current_p, action] += self.learning_rate * (
                reward + self.discount_factor * np.max(self.q_table[new_state]) - self.q_table[current_p, action])

        # print("new value of self.q_table[%s, %s] is %s" % (current_p, action, self.q_table[current_p, action]))
        return new_state
