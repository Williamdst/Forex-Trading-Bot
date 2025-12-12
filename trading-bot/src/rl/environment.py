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
        prices: np.ndarray,
        initial_balance: float=1000,
        window_size: int=10,
        render_mode=None
    ):
        super().__init__()

        assert isinstance(prices, np.ndarray) and prices.ndim == 1 and len(prices) >= 2, \
            "prices must be a 1D numpy array with length >= 2"

        self.prices = prices.astype(np.float32)
        self.initial_balance = float(initial_balance)
        self.window_size = int(window_size)

        # --- State that changes during an episode ---
        self.current_balance = float(self.initial_balance)
        self.trade_entry_price = None  # float or None
        self.current_step = 0  # start at 0 (first price index)
        self.num_trades = 0
        self.current_position_type = Position.EMPTY
        self.current_unrealized_pnl = np.float32(0.0)

        # Actions: hold, buy, sell, close
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Dict({
            "market": spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(self.window_size,),
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

    # ----------------------------
    # Helper functions
    # ----------------------------
    def _normalized_unrealized(self) -> np.float32:
        # normalize by initial_balance and clip into [-1, 1] for observation (not for reward)
        val = 0.0 if self.current_unrealized_pnl is None else float(self.current_unrealized_pnl)
        normalized = np.float32(np.clip(val / max(1.0, self.initial_balance), -1.0, 1.0))
        return normalized

    def reset(self, seed=None, options=None):
        # TODO: MY RESET SHOULD RESET PRICE ARRAY FROM GAN

        self.current_balance = float(self.initial_balance)
        self.trade_entry_price = None
        self.current_step = 0
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
                "open_position": np.int64(self.current_position_type.value)
            }
        }

        return observation, {}



    def step(self, action):
        """
        Core step function.
        Order of operations:
         1. Determine current price (prices[idx]) and whether a next price exists (next_idx).
         2. Save previous unrealized pnl for delta reward calculation.
         3. Apply action which may open or close at the CURRENT price (closing realizes at current price).
         4. If this is the last step (no next price), force-close any open position at current price and end truncated.
         5. Otherwise, simulate price movement to next_price and update unrealized PnL accordingly.
         6. Compute reward:
              - If we realized (explicit close or forced final close): reward = realized_pnl / initial_balance
              - Else reward = change_in_unrealized_pnl / initial_balance
         7. Advance step index (cap to last index).
         8. Build next observation and return.
        """
        reward = 0.0
        terminated = False
        truncated = False
        info = {}

        idx = self.current_step
        next_idx = idx + 1
        has_next_idx = next_idx < len(self.prices)
        is_last_step = not has_next_idx

        current_price = float(self.prices[idx])
        next_price = float(self.prices[next_idx]) if has_next_idx else current_price
        prev_unrealized_pnl = float(self.current_unrealized_pnl)

        invalid_action_penalty = -0.01 * self.initial_balance
        if not self.action_space.contains(action):
            raise ValueError(f"Received invalid action={action}")

        # NOTE: SETTING CURRENT_UNREALIZED_PNL IS FOR THE NEXT STEP
        if self.current_position_type == Position.EMPTY:
            if action == 0: reward = 0.0
            elif action == 3: reward  = invalid_action_penalty

            else:
                self.trade_entry_price = current_price
                self.num_trades += 1
                reward = 0.0

                if action == 1:
                    self.current_position_type = Position.LONG
                elif action == 2:
                    self.current_position_type = Position.SHORT
        elif (
            self.current_position_type == Position.LONG
            or self.current_position_type == Position.SHORT
        ):
            if action == 1 or action == 2: reward = invalid_action_penalty
            else:
                # TODO HOW TO DO DELTA REWARD TO MAKE IT SUMMABLE?
                reward = self.current_unrealized_pnl

                if action == 0: pass
                if action == 3:
                    self.current_balance += self.current_unrealized_pnl

                    # Reset
                    self.current_position_type = Position.EMPTY
                    self.trade_entry_price = None

        # TODO: THE TRUNCATION LOGIC
        if is_last_step:
            truncated = True

        if self.current_position_type == Position.LONG:
            self.current_unrealized_pnl = float(next_price - self.trade_entry_price)
        elif self.current_position_type == Position.SHORT:
            self.current_unrealized_pnl = float(self.trade_entry_price - next_price)
        else:
            self.current_unrealized_pnl = 0.0

        # TODO: FIGURE OUT REWARD STUFF


        self.current_step = min(next_idx, len(self.prices) - 1)
        if self.current_balance <= 0:
            terminated = True

        new_return = np.log(self.prices[next_idx] / self.prices[idx])
        observation = {
            "market": np.array([new_return], dtype=np.float32),
            "trade": {
                "unrealized_pnl": np.float32(self.current_unrealized_pnl),
                "open_position": np.int64(self.current_position_type.value)
            }
        }

        return observation, reward, terminated, truncated, {}



if __name__ == "__main__":
    env = SimpleTradingEnv(
        prices=np.array([100, 110, 150, 200, 250])
    )
    obs, info = env.reset()

    obs, reward, terminated, truncated, info = env.step(action=1)
    print(obs, reward)
    print(env.__dict__)
    print()

    obs, reward, terminated, truncated, info = env.step(action=3)
    print(obs, reward)
    print(env.__dict__)
    print()

    obs, reward, terminated, truncated, info = env.step(action=1)
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