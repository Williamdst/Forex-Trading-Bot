# Trading Bot: Aggregated Marginal Gains

This project is a personal exploration into scaling algorithmic trading by focusing on small, consistent gains across multiple instruments. Instead of hunting for high-alpha strategies on a single pair, this approach aims for modest, reliable returns (1-3% annually) spread across a wide portfolio.

## Project Thesis

Automation is the key to scaling small wins. For a \$1,000 account, a 1–3% annual return is only \$10–\$30 (roughly 100–300 pips). While this is a very achievable target for a human trader, doing it manually across dozens of currency pairs is exhausting and impractical. 

By automating this process, we can target these small returns across all major pairs simultaneously. This scales the aggregate return (e.g., 7-21%) without needing to increase the complexity or risk of the underlying strategy.

## Trading Strategy

The core challenge is still finding a winning logic, but by lowering the bar for target returns, we open up more possibilities. Simple strategies that might not be "profitable enough" for high-yield targets can become very effective in high-probability, low-yield scenarios.

## Risk Management

To keep things simple and safe, I use a standardized risk model: every position is limited to a fixed 1% risk of total account equity.