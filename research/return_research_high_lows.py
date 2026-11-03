try:
  import unzip_requirements
except ImportError:
  pass

import os
from dotenv import load_dotenv

from src.infrastructure.snowflake import SnowflakeClient

load_dotenv()

def generate_trades(candles: list, instrument: str):
    pip_multiplier = 10000 if 'JPY' not in instrument else 100
    trades = []
    current_trade = {}
    for candle in candles:
        if candle['DID_DIRECTION_SHIFT'] == True:
            new_trade = {
                'instrument': candle['INSTRUMENT'],
                'brick_number': candle['BRICK_NUMBER'],
                'direction': candle['BRICK_TYPE'],
                'open': candle['ASK_CLOSE'] if candle['BRICK_TYPE'] == 'LONG' else candle['BID_CLOSE'],
                'brick_open': candle['BRICK_CLOSE'],
                'max_opposite': candle['BRICK_CLOSE'],
                'max_direction': candle['BRICK_CLOSE'],
                'close': None
            }

            if not current_trade:
                current_trade = new_trade
                continue

            current_trade['max_stop_loss'] = abs(current_trade['open'] - current_trade['max_opposite']) * pip_multiplier
            current_trade['max_take_profit'] = abs(current_trade['open'] - current_trade['max_direction']) * pip_multiplier
            current_trade['tp_sl_spread'] = current_trade['max_take_profit'] - current_trade['max_stop_loss']
            current_trade['close'] = candle['BID_CLOSE'] if current_trade['direction'] == 'LONG' else candle['ASK_CLOSE']

            if current_trade['direction'] == 'LONG':
                current_trade['pip_profit'] = (current_trade['close'] - current_trade['open']) * pip_multiplier
            elif current_trade['direction'] == 'SHORT':
                current_trade['pip_profit'] = (current_trade['open'] - current_trade['close']) * pip_multiplier

            trades.append(current_trade)
            current_trade = new_trade

        elif (
            current_trade
        ):
            if current_trade['direction'] == 'LONG':
                if candle['BID_HIGH'] >= current_trade['max_direction']:
                    current_trade['max_direction'] = candle['BID_HIGH']

                if candle['BID_LOW'] <= current_trade['max_opposite']:
                    current_trade['max_opposite'] = candle['BID_LOW']

            elif current_trade['direction'] == 'SHORT':
                if candle['ASK_LOW'] <= current_trade['max_direction']:
                    current_trade['max_direction'] = candle['ASK_LOW']

                if candle['ASK_HIGH'] >= current_trade['max_opposite']:
                    current_trade['max_opposite'] = candle['ASK_HIGH']

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

    trades = generate_trades(trend_data, instrument)
    delete_query = f"""
        DELETE FROM PRODUCTION.DATA.HOUR1_RENKO_BRICK_TRADES
        WHERE instrument = '{instrument}'
    """
    SNOWFLAKE.run_query(delete_query)

    insert_sql = f"""
        INSERT INTO 
        PRODUCTION.DATA.HOUR1_RENKO_BRICK_TRADES (
            instrument, brick_number, direction, open, brick_open,
            max_opposite, max_directon, close, max_stop_loss, max_take_profit,
            tp_sl_spread, pip_profit
        )
        VALUES (
            %(instrument)s, %(brick_number)s, %(direction)s, %(open)s, %(brick_open)s,
            %(max_opposite)s, %(max_direction)s, %(close)s, %(max_stop_loss)s,
            %(max_take_profit)s, %(tp_sl_spread)s, %(pip_profit)s
        )
        """

    SNOWFLAKE.execute_many(insert_sql, trades)


if __name__ == "__main__":
    test_event = {
        'instrument': 'EUR_USD',
        'starting_balance': 1000
    }
    lambda_handler(test_event, None)