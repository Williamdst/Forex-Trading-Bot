import os
from dotenv import load_dotenv

from integrations.snowflake import SnowflakeClient

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
    AWS Lambda handler function to retrieve a list of distinct instruments
    from a Snowflake database.

    Parameters:
    - event (dict): Event data passed to the Lambda function.
    - context (LambdaContext): Runtime information provided by AWS Lambda.

    Returns:
    - list: A list of distinct instrument names retrieved from the
        Snowflake database.
    """
    instruments = SNOWFLAKE.run_query(
        """
        SELECT DISTINCT instrument FROM PRODUCTION.APPLICATION.INSTRUMENTS
        WHERE is_active
        """
    )
    return [_[0] for _ in instruments]

if __name__ == "__main__":
    test_event = {}
    result = lambda_handler(test_event, None)
    print(result)
