try:
  import unzip_requirements
except ImportError:
  pass

import os
from dotenv import load_dotenv

from infrastructure.snowflake import SnowflakeClient
from domain.renko_generator import generate_renko_bricks

load_dotenv()
SNOWFLAKE = SnowflakeClient(
    user=os.environ["SNOWFLAKE_USERNAME"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    schema=os.environ["SNOWFLAKE_SCHEMA"],
    warehouse="compute_wh"
)

def lambda_handler(event, context):
    """
    """
    print("Received event:", event)
    try:
        event = event['Payload']
    except KeyError:
        pass

    instrument = event['instrument'].upper()

    ohlc_data = SNOWFLAKE.run_query(
        query=(f"""
            SELECT * 
            FROM PRODUCTION.DATA.DIM_OANDA_HOUR1_FOREX_CANDLES
            WHERE instrument = '{instrument}' 
                AND is_candle_complete 
            ORDER BY candle_open_time ASC
        """
        ),
        use_dict_cursor=True
    )

    # The initial brick needs to be an artificial value one below the start value
    brick_config = SNOWFLAKE.run_query(
        query=(f"""
            SELECT
                instrument,
                artificial_brick_open, 
                artificial_brick_close, 
                brick_type,
                brick_size
            FROM PRODUCTION.APPLICATION.INSTRUMENTS
            WHERE instrument = '{instrument}'
        """
        ),
        use_dict_cursor=True
    )

    renko_bricks = generate_renko_bricks(
        candles=ohlc_data,
        brick_config={
            'instrument': brick_config[0]['INSTRUMENT'],
            'artificial_brick_open': brick_config[0]['ARTIFICIAL_BRICK_OPEN'],
            'artificial_brick_close': brick_config[0]['ARTIFICIAL_BRICK_CLOSE'],
            'brick_type': brick_config[0]['BRICK_TYPE'],
            'brick_size': brick_config[0]['BRICK_SIZE']
        },
        return_dicts=False
    )

    SNOWFLAKE.run_query(
        query=(f"""
            DELETE FROM PRODUCTION.DATA.HOUR1_RENKO_BRICKS
            WHERE instrument = '{instrument}'
        """)
    )

    response = SNOWFLAKE.execute_many(
        query="""
        INSERT INTO PRODUCTION.DATA.HOUR1_RENKO_BRICKS(
          instrument, candle_open_time, candle_close_time, open, close, 
          brick_type, streak_order, brick_number, high, low
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        values=renko_bricks
    )

    return {
        'statusCode': 200 if response[0] else 500,
        'body': response
    }


if __name__ == "__main__":
    test_event = {
        'instrument': 'EUR_USD'
    }
    print(lambda_handler(test_event, None))
