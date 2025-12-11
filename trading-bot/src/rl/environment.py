from enum import Enum
import gymnasium as gym
from gymnasium import spaces

import numpy as np

class Position(Enum):
    EMPTY = 0
    LONG = 1
    SHORT = 2

class SimpleTradingEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        prices: np.array,
        initial_balance: np.float32=1000,
        render_mode=None
    ):
        super().__init__()

        self.prices = prices                # np.array of prices (close)
        self.initial_balance = initial_balance

        # Things that will change during the episode
        self.current_balance = initial_balance
        self.trade_entry_price = None
        self.current_step = 1
        self.num_trades = 0
        self.current_position_type = Position.EMPTY
        self.current_unrealized_pnl = np.float32(0.0)

        # Actions: hold, buy, sell, close
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Dict({
            "market": spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(1,),
                dtype=np.float32
            ),
            "trade": gym.spaces.Dict({
                "unrealized_pnl": gym.spaces.Box(
                    low=-1.0,
                    high=1.0,     # % of account balance (bounded reward scale)
                    shape=(),
                    dtype=np.float32
                ),
                # none (0), long (1), short (2)
                "open_position": gym.spaces.Discrete(3)
            })
        })

    def reset(self, seed=None, options=None):
        # TODO: MY RESET SHOULD RESET PRICE ARRAY FROM GAN

        self.current_balance = float(self.initial_balance)
        self.trade_entry_price = None
        self.current_step = 1

        self.num_trades = 0
        self.current_position_type = Position.EMPTY
        self.current_unrealized_pnl = np.float32(0.0)

        init_return = (
            np.log(self.prices[self.current_step] / self.prices[self.current_step - 1])
        )

        observation = {
            "market": np.array([init_return], dtype=np.float32),
            "trade": {
                "unrealized_pnl": np.float32(0.0),
                "open_position": np.int64(Position.EMPTY.value)
            }
        }

        return observation, {}



    def step(self, action):
        reward = 0.0
        terminated = False
        truncated = False

        if self.current_position_type == Position.EMPTY:
            if action == 4: reward = -10.0
            elif action == 0: reward = 0.0
            else:
                self.trade_entry_price = self.prices[self.current_step]
                self.num_trades += 1

                if action == 1:
                    self.current_position_type = Position.LONG
                    self.current_unrealized_pnl = self.prices[self.current_step + 1] - self.trade_entry_price

                elif action == 2:
                    self.current_position_type = Position.SHORT
                    self.current_unrealized_pnl = self.trade_entry_price - self.prices[self.current_step + 1]

                reward = self.current_unrealized_pnl

        elif self.current_position_type == Position.LONG:
            if action in (1, 2): reward = -10.0

            # Hold Position
            elif action == 0:
                previous_unrealized_pnl = self.current_unrealized_pnl
                self.current_unrealized_pnl = self.prices[self.current_step + 1] - self.trade_entry_price
                reward = self.current_unrealized_pnl - previous_unrealized_pnl

            # Close Position
            elif action == 3:
                total_profit = self.prices[self.current_step] - self.trade_entry_price
                self.current_balance += total_profit

                reward = 0.0
                self.current_unrealized_pnl = 0.0
                self.current_position_type = Position.EMPTY
                self.trade_entry_price = None

        elif self.current_position_type == Position.SHORT:
            if action in (1, 2): reward = -10.0

            # Hold Position
            elif action == 0:
                previous_unrealized_pnl = self.current_unrealized_pnl
                self.current_unrealized_pnl = self.trade_entry_price - self.prices[self.current_step + 1]
                reward = self.current_unrealized_pnl - previous_unrealized_pnl

            # Close Position
            elif action == 3:
                total_profit = self.trade_entry_price - self.prices[self.current_step]
                self.current_balance += total_profit

                reward = 0.0
                self.current_unrealized_pnl = 0.0
                self.current_position_type = Position.EMPTY
                self.trade_entry_price = None

        new_return = (
            np.log(self.prices[self.current_step+1] / self.prices[self.current_step])
        )
        observation = {
            "market": np.array([new_return], dtype=np.float32),
            "trade": {
                "unrealized_pnl": np.float32(self.current_unrealized_pnl),
                "open_position": np.int64(self.current_position_type.value)
            }
        }
        self.current_step += 1

        if self.current_balance <= 0:
            terminated = True

        if self.current_step == len(self.prices):
            truncated = True

        return observation, reward, terminated, truncated, {}



if __name__ == "__main__":
    env = SimpleTradingEnv(
        prices=np.array([100, 110, 150, 200, 250])
    )
    obs, info = env.reset()

    obs, reward, terminated, truncated, info = env.step(action=2)
    print(obs, reward)
    print(env.__dict__)
    print()

    obs, reward, terminated, truncated, info = env.step(action=0)
    print(obs, reward)
    print(env.__dict__)
    print()

    obs, reward, terminated, truncated, info = env.step(action=3)
    print(obs, reward)
    print(env.__dict__)
    print()