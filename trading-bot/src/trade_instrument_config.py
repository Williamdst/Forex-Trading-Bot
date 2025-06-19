import os
from dotenv import load_dotenv

from infrastructure.snowflake import SnowflakeClient

load_dotenv()
SNOWFLAKE = SnowflakeClient(
    user=os.environ["SNOWFLAKE_USERNAME"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    schema=os.environ["SNOWFLAKE_SCHEMA"],
    warehouse="compute_wh"
)

# For every instrument, I need to check if the current candle has a renko brick
# with a direction change.
def lambda_handler(event, context):
    """
    """
    instruments = SNOWFLAKE.run_query(
        query="""
        SELECT
          d.instrument,
          d.brick_type as direction
        FROM PRODUCTION.DATA.TS_HOUR1_RENKO_OHLC AS d
        INNER JOIN PRODUCTION.APPLICATION.INSTRUMENTS AS i
          ON d.instrument = i.instrument
        WHERE i.is_active
          AND d.is_candle_complete = FALSE
          AND d.did_direction_shift = TRUE
        """,
        use_dict_cursor=True
    )
    return instruments

if __name__ == "__main__":
    test_event = {}
    print(lambda_handler(test_event, None))
