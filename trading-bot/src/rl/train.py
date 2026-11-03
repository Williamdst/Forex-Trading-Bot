# Example: synthetic data or load real data
import numpy as np
from gymnasium.wrappers import FlattenObservation
from rl.environment import SimpleTradingEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv


# Synthetic random walk
def generate_prices(n_steps=1000, start_price=100):
    returns = np.random.randn(n_steps) * 0.02  # 2% daily volatility
    prices = start_price * np.exp(np.cumsum(returns))
    return prices

train_prices = generate_prices(10000)

# env = SimpleTradingEnv(prices=train_prices)
# env = FlattenObservation(env)
env = DummyVecEnv([lambda: FlattenObservation(SimpleTradingEnv(train_prices))])

# Initialize agent
model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64
    # tensorboard_log="./trading_tensorboard/"
)

# Train
model.learn(total_timesteps=100_000)
model.save("trading_agent")