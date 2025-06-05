try:
  import unzip_requirements
except ImportError:
  pass

import os
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

from integrations.snowflake import SnowflakeClient
from integrations.renko import generate_renko_bricks

load_dotenv()

def lambda_handler(event, context):
    """
    """
    print("Received event:", event)
    try:
        event = event['Payload']
    except KeyError:
        pass

    SNOWFLAKE = SnowflakeClient(
        user=os.environ["SNOWFLAKE_USERNAME"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        warehouse="compute_wh"
    )

    try:
        instrument = event['instrument'].upper()
    except KeyError:
        return {
            'statusCode': 400,
            'body': 'Missing required parameters'
        }

    ohlc_data = SNOWFLAKE.run_query(
        query=(f"""
            SELECT * 
            FROM PRODUCTION.DATA.DIM_OANDA_HOUR1_FOREX_CANDLES
            WHERE instrument = '{instrument}' 
                AND is_candle_complete 
            ORDER BY candle_open_time ASC
        """
        ),
        use_pandas=True
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
        )
    )
    renko_bricks = generate_renko_bricks(
        df=ohlc_data,
        brick_config={
            'instrument': brick_config[0][0],
            'artificial_brick_open': float(brick_config[0][1]),
            'artificial_brick_close': float(brick_config[0][2]),
            'brick_type': brick_config[0][3],
            'brick_size': float(brick_config[0][4])
        }
    )

    SNOWFLAKE.run_query(
        query=(f"""
            DELETE FROM PRODUCTION.DATA.HOUR1_RENKO_BRICKS
            WHERE instrument = '{instrument}'
        """)
    )

    response = write_pandas(
        conn=SNOWFLAKE.connection,
        df=renko_bricks,
        table_name='HOUR1_RENKO_BRICKS',
        database='PRODUCTION',
        schema='DATA'
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
