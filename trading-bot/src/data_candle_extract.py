import os
from dotenv import load_dotenv

from integrations.oanda import OandaClient
from integrations.snowflake import SnowflakeClient

load_dotenv()


def lambda_handler(event, context):
    """
    AWS Lambda handler function to fetch candle data for a specified instrument from Oanda

    Parameters:
    - event (dict): Event data passed to the Lambda function
    - context (LambdaContext): Runtime information provided by AWS Lambda

    Returns:
    - dict: API response containing status code and transformed candle data
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

    OANDA = OandaClient(
        api_key=os.getenv("OANDA_API_KEY"),
        account_id='001-001-10122498-001',
        is_demo=False
    )

    try:
        instrument = event['instrument'].upper()
        granularity = event.get('granularity', 'H1').upper()
        count = event.get('count', 2)
        from_date = event.get('from_date', None)
        to_date = event.get('to_date', None)
    except KeyError:
        return {
            'statusCode': 400,
            'body': 'Missing required parameters'
        }

    params = {
        'price': 'MBA',
        'granularity': granularity
    }
    if from_date and to_date:
        params['from'] = from_date
        params['to'] = to_date
    elif from_date:
        params['from'] = from_date
    else:
        params['count'] = count

    candle_data = OANDA.send_request(
        method='GET',
        endpoint=f'instruments/{instrument}/candles',
        params=params
    ).json()


    transformed = [
        {
            **{k: candle[k] for k in ['complete', 'volume', 'time']},
            **{
                f'{pt}_{k}': v for pt in ['bid', 'mid', 'ask'] for
                k, v in candle[pt].items()
            },
            'instrument': candle_data['instrument'],
            'granularity': candle_data['granularity']
        }
        for candle in candle_data['candles']
    ]

    data_map = {
        'H1': 'HOUR1'
    }

    insert_sql = f"""
    INSERT INTO 
    {os.environ["SNOWFLAKE_DATABASE"]}.DATA
    .OANDA_{data_map[granularity]}_FOREX_CANDLES (
        instrument, granularity, candle_open_time, is_candle_complete, volume,
        ask_open, ask_high, ask_low, ask_close, 
        bid_open, bid_high, bid_low, bid_close, 
        mid_open, mid_high, mid_low, mid_close
    )
    VALUES (
        %(instrument)s, %(granularity)s, %(time)s, %(complete)s, %(volume)s,
        %(ask_o)s, %(ask_h)s, %(ask_l)s, %(ask_c)s,
        %(bid_o)s, %(bid_h)s, %(bid_l)s, %(bid_c)s,
        %(mid_o)s, %(mid_h)s, %(mid_l)s, %(mid_c)s
    )
    """

    SNOWFLAKE.execute_many(insert_sql, transformed)
    return None

if __name__ == "__main__":
    for instrument in [
        'EUR_USD', 'USD_CAD', 'GBP_USD', 'USD_CHF',
        'AUD_USD', 'NZD_USD', 'USD_JPY'
    ]:
        test_event = {
            'instrument': instrument,
            'granularity': 'H1',
            'count': 10
            # 'from_date': '2025-05-01T00:00:00Z'
        }
        result = lambda_handler(test_event, None)

