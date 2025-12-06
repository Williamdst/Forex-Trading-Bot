<h1>RL Trading Bot Specification</h1>
I want to use gymnasium to train a rl trading bot:

<h2> Action Space </h2>
Do Nothing (0), Buy (1), Sell (2), Close Position (3)

Rules:
- Only a single trade can be open on an instrument at any time. You cannot buy or sell if there is already a position open.
- No partial trades or trade stacking allowed.
- Trades do not have to be open at all times; the bot can choose to do nothing and not trade.
- Trades cannot be reversed directly; a position must be closed before opening a new one.
- Trades must be executed in the following sequence: Open → Close → Open over three timesteps.
- You cannot close a position if there is no open trade.

For simplicity to start, if the bot tries to take an invalid action (e.g., trying to buy when a buy position is 
already open), the environment should give out a negative reward of -10 and move to the next timestep. Ideally, we 
want to use action masking to prevent invalid actions from being chosen and not mess with the reward structure, but 
that is too complex for now.


<h2> Training Ends </h2>
The training ends when the account balance is depleted or when all the data has been exhausted.

When the data is exhausted, the final reward should be 0 because the

- When dealing with the prices array, we start the training with an index of 1 because we need to calculate the 
  return from price[0] to price[1] for the first observation. Which means termination happens when the index reaches 
  the length of the prices array.

<h2> Reward Structure </h2>
The reward trying to be maximized is the profit of the trades executed normalized to the account balance. In each timestep the reward is calculated as follows:

- When a trade is opened (buy/sell), the reward is the unrealized pnl as the price changes going to the next step.
- When there isn't a trade open and the action is do nothing, the reward is 0.
- When there is a trade open and the action is to do nothing or close the trade, the reward is the difference 
  between the current unrealized pnl of the open trade minus the previous unrealized pnl of that trade. Then 
  normalized to the account balance. Note: In the case of closing a trade, the unrealized pnl turns into the 
  realized pnl, but the reward is still calculated as the difference between the realized pnl and the previous 
  unrealized pnl. Note: the first timestep after opening a trade, the previous unrealized pnl is 0, so the reward is just the current unrealized pnl normalized to the account

<h2> Environment Dynamics </h2>



- Account balance when the trade was opened (to normalize pnl). Once a trade is closed and the pnl is normalized this value is reset to NULL. This is why this is in the environment dynamics and not in the observation space.
- Last unrealized pnl (to calculate reward) 
- The number of trades taken in the episode (to track performance).
- The actual profit/loss made in the episode (to track performance).
- The environment should take in prices values and will calculate the natural LOG returns internally. We use prices for 
  calculating pnl but returns for the observation space.


<h2> Observation Space </h2>
the returns of the last N timesteps
unrealized pnl (percentage of account balance)
what is the current open position: none, buy, sell

The observation space should use dictionary spacing where the returns are in one key and as an array of floats, and the normalized unrealized pnl is in another key as a single float along with the current open position as an integer (0: none, 1: buy, 2: sell).

Use a `_get_obs` function to return the observation space as a dictionary with the specified keys and values.
Use a `_get_info` function to return additional information about the environment's state, such as the current account balance, number of trades taken, and total profit/loss made in the episode.
