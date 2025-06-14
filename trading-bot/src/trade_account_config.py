try:
  import unzip_requirements
except ImportError:
  pass

import os
from dotenv import load_dotenv

from integrations.snowflake import SnowflakeClient
from integrations.renko import generate_renko_bricks

load_dotenv()
SNOWFLAKE = SnowflakeClient(
    user=os.environ["SNOWFLAKE_USERNAME"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    schema=os.environ["SNOWFLAKE_SCHEMA"],
    warehouse="compute_wh"
)

# I need to get all the active accounts that have a configuration for that instrument
def lambda_handler(event, context):
    """
    """
    print("Received event:", event)
    try:
        event = event['Payload']
    except KeyError:
        pass

    instrument = event['instrument'].upper()
    account_configs = SNOWFLAKE.run_query(
        query=(f"""
            SELECT
              a.account_id,
              a.platform_id,
              i.instrument,
              a.api_key_id,
              a.is_live_account,
              aic.position_sizing_type,
              aic.position_sizing_value
            FROM PRODUCTION.APPLICATION.ACCOUNTS AS a
            LEFT JOIN PRODUCTION.APPLICATION.account_instruments_config AS aic
              ON a.account_id = aic.account_id
            LEFT JOIN production.application.instruments as i
              ON aic.instrument_id = i.instrument_id
            WHERE a.is_active
              AND aic.is_active
              AND i.instrument = '{instrument}'
        """
        ),
        use_dict_cursor=True
    )

    return account_configs


if __name__ == "__main__":
    test_event = {
        'instrument': 'EUR_USD'
    }
    print(lambda_handler(test_event, None))
