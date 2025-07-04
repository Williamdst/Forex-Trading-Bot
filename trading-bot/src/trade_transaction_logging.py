import json
import os
import boto3
from dotenv import load_dotenv
from datetime import datetime

from infrastructure.oanda import OandaClient
from infrastructure.snowflake import SnowflakeClient

from services.config_service import ConfigProvider

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
    try:
        event = event['Payload']
    except KeyError:
        pass

    account_id = event['ACCOUNT_ID']
    config_service = ConfigProvider(SNOWFLAKE)
    oanda_credentials = config_service.get_account_credentials(
        account_id=account_id
    )
    OANDA = OandaClient(
        account_id=oanda_credentials['PLATFORM_ID'],
        api_key=oanda_credentials['API_KEY'],
        is_live=oanda_credentials['IS_LIVE_ACCOUNT']
    )

    # TODO: QUERY THE LATEST TRANSACTION ID FROM SNOWFLAKE
    response = OANDA.send_request(
        method='GET',
        endpoint='transactions/sinceid',
        params={
            'id': 0
        }
    ).json()

    s3 = boto3.client('s3')
    s3.put_object(
        Bucket="ict-trading-bot",
        Key=(
            f"account_logs/oanda/"
            f"{oanda_credentials['PLATFORM_ID']}_transactions_"
            f"{datetime.utcnow()}.json"
        ),
        Body=json.dumps(response),
        ContentType='application/json'
    )

    return None


if __name__ == "__main__":
    test_event = {
        'ACCOUNT_ID': 1
    }
    lambda_handler(test_event, None)
