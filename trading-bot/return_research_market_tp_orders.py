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
    new_trade = {}
    for candle in candles:
        if candle['DID_DIRECTION_SHIFT'] == True:
            new_trade = {
                'brick_number': candle['BRICK_NUMBER'],
                'direction': candle['BRICK_TYPE'],
                'open': float(candle['ASK_CLOSE']) if candle['BRICK_TYPE'] == 'LONG' else float(candle['BID_CLOSE']),
                'brick_open': float(candle['BRICK_CLOSE']),
                'tp': float(candle['ASK_CLOSE']) + 0.0040 if candle['BRICK_TYPE'] == 'LONG' else float(candle['BID_CLOSE']) - 0.0040,
                'close': None
            }

            if not current_trade:
                current_trade = new_trade
                continue

            if current_trade['close'] is None:
                current_trade['close'] = float(candle['BID_CLOSE']) if current_trade['direction'] == 'LONG' else float(candle['ASK_CLOSE'])
                current_trade['brick_close'] = float(candle['BRICK_CLOSE'])

            if current_trade['direction'] == 'LONG':
                current_trade['pip_profit'] = current_trade['close'] - current_trade['open']
                current_trade['open_drift'] = current_trade['brick_open'] - current_trade['open']
                # current_trade['close_drift'] = current_trade['close'] - current_trade['brick_close']
            elif current_trade['direction'] == 'SHORT':
                current_trade['pip_profit'] = current_trade['open'] - current_trade['close']
                current_trade['open_drift'] = current_trade['open'] - current_trade['brick_open']
                # current_trade['close_drift'] = current_trade['brick_close'] - current_trade['close']

            trades.append(current_trade)
            current_trade = new_trade

        # Checking to see if sl/tp is hit
        elif (
            current_trade
            and current_trade['close'] is None
        ):
            if current_trade['direction'] == 'LONG':
                if candle['BID_HIGH'] >= current_trade['tp']:
                    current_trade['close'] = current_trade['tp']

            elif current_trade['direction'] == 'SHORT':
                if candle['ASK_LOW'] <= current_trade['tp']:
                    current_trade['close'] = current_trade['tp']

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
            FROM production.DATA.ts__hour1_renko_ohlc
            WHERE instrument = '{instrument}'
            order by CANDLE_NUMBER asc
        """
        ),
        use_dict_cursor=True
    )

    trades = generate_trades(trend_data)
    print(trades)

    current_balance = starting_balance
    for trade_num, trade in enumerate(trades, 1):
        pip_value = current_balance / 10000
        total_pips = float(trade['pip_profit'] * 10000)  # Convert to pips
        earned = total_pips * pip_value
        new_balance = current_balance + earned
        # print(
        #     f"trade_num: {trade_num}, pips_made: {total_pips} "
        #     f"pip_value: {pip_value}, balance: {new_balance}, earned: {earned}"
        # )
        current_balance = new_balance


if __name__ == "__main__":
    test_event = {
        'instrument': 'EUR_USD',
        'starting_balance': 1000
    }
    lambda_handler(test_event, None)