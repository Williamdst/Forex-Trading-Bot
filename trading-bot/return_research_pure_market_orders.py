try:
  import unzip_requirements
except ImportError:
  pass

import os
from dotenv import load_dotenv

from src.infrastructure.snowflake import SnowflakeClient

load_dotenv()

def generate_trades(candles: list):
    trades = []
    current_trade = {}
    for candle in candles:
        if candle['DID_DIRECTION_SHIFT'] != True:
            continue

        # Create a new trade entry
        new_trade = {
            'brick_number': candle['BRICK_NUMBER'],
            'direction': candle['BRICK_TYPE'],
            'open': candle['ASK_CLOSE'] if candle['BRICK_TYPE'] == 'LONG' else
            candle['BID_CLOSE'],
            'brick_open': candle['BRICK_CLOSE'],
            'close': None,
            'brick_close': None
        }

        # For the first trade only
        if not current_trade:
            current_trade = new_trade
            continue

        # If the direction has changed, close the current trade
        current_trade['close'] = candle['BID_CLOSE'] if current_trade[
                                                            'direction'] == 'LONG' else \
        candle['ASK_CLOSE']
        current_trade['brick_close'] = candle['BRICK_CLOSE']

        if current_trade['direction'] == 'LONG':
            current_trade['pip_profit'] = current_trade['close'] - \
                                          current_trade['open']
            current_trade['open_drift'] = current_trade['brick_open'] - \
                                          current_trade['open']
            current_trade['close_drift'] = current_trade['close'] - \
                                           current_trade['brick_close']

        elif current_trade['direction'] == 'SHORT':
            current_trade['pip_profit'] = current_trade['open'] - current_trade[
                'close']
            current_trade['open_drift'] = current_trade['open'] - current_trade[
                'brick_open']
            current_trade['close_drift'] = current_trade['brick_close'] - \
                                           current_trade['close']

        trades.append(current_trade)
        current_trade = new_trade

    return trades


def lambda_handler(event, context):
    """
    """
    SNOWFLAKE = SnowflakeClient(
        user=os.environ["SNOWFLAKE_USERNAME"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        warehouse="compute_wh"
    )

    instrument = event['instrument'].upper()
    starting_balance = event['starting_balance']

    trend_data = SNOWFLAKE.run_query(
        query=(f"""
            SELECT * 
            FROM PRODUCTION.DATA.ts__hour1_renko_ohlc
            WHERE instrument = '{instrument}'
            order by candle_open_time asc
        """
        ),
        use_dict_cursor=True
    )

    trades = generate_trades(trend_data)

    current_balance = starting_balance
    for trade_num, trade in enumerate(trades, 1):
        pip_value = current_balance / 10000
        total_pips = float(trade['pip_profit'] * 10000)  # Convert to pips
        earned = total_pips * pip_value
        new_balance = current_balance + earned
        print(
            f"trade_num: {trade_num}, pips_made: {total_pips} "
            f"pip_value: {pip_value}, balance: {new_balance}, earned: {earned}"
        )
        current_balance = new_balance


if __name__ == "__main__":
    test_event = {
        'instrument': 'AUD_USD',
        'starting_balance': 1000
    }
    lambda_handler(test_event, None)