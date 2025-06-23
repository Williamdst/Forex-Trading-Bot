try:
  import unzip_requirements
except ImportError:
  pass

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

def lambda_handler(event, context):
    """
    """
    print("Received event:", event)
    try:
        event = event['Payload']
    except KeyError:
        pass

    instrument = event['INSTRUMENT'].upper()
    account_configs = SNOWFLAKE.run_query(
        query=(f"""
            SELECT DISTINCT
              a.account_id
            FROM PRODUCTION.APPLICATION.ACCOUNTS AS a
            LEFT JOIN PRODUCTION.APPLICATION.ACCOUNT_INSTRUMENTS_CONFIG AS aic
              ON a.account_id = aic.account_id
            LEFT JOIN PRODUCTION.APPLICATION.INSTRUMENTS as i
              ON aic.instrument_id = i.instrument_id
            WHERE a.is_active
              AND aic.is_active
              AND i.instrument = '{instrument}'
        """
        )
    )

    return [_[0] for _ in account_configs]


if __name__ == "__main__":
    test_event = {
        'INSTRUMENT': 'EUR_USD'
    }
    print(lambda_handler(test_event, None))
