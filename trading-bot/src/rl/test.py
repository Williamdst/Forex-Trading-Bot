from stable_baselines3 import PPO
from gymnasium.wrappers import FlattenObservation
import numpy as np
from rl.environment import SimpleTradingEnv

# Synthetic random walk
def generate_prices(n_steps=1000, start_price=100):
    returns = np.random.randn(n_steps) * 0.02  # 2% daily volatility
    prices = start_price * np.exp(np.cumsum(returns))
    return prices

# Load the trained model
model = PPO.load("trading_agent")

# Create test environment with NEW price data
test_prices = generate_prices(2000)  # Different from training data
env = FlattenObservation(SimpleTradingEnv(test_prices))

# Run evaluation
obs, info = env.reset()
total_reward = 0
done = False

while not done:
    action, _states = model.predict(obs, deterministic=True)
    print(action, _states)
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    done = terminated or truncated

print(f"Total Reward: {total_reward}")
print(f"Final Balance: {env.unwrapped.current_balance}")
print(f"Number of Trades: {env.unwrapped.num_trades}")