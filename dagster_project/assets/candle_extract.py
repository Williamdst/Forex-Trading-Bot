import os
from dagster import EnvVar, asset, AssetExecutionContext

from ..integrations.oanda import OandaClient
from ..integrations.snowflake import SnowflakeClient


@asset
def lambda_handler(context:AssetExecutionContext):
    """
    AWS Lambda handler function to fetch candle data for a specified instrument from Oanda

    Parameters:
    - event (dict): Event data passed to the Lambda function
    - context (LambdaContext): Runtime information provided by AWS Lambda

    Returns:
    - dict: API response containing status code and transformed candle data
    """
    SNOWFLAKE = SnowflakeClient(
        user=EnvVar("SNOWFLAKE_USERNAME").get_value(),
        password=EnvVar("SNOWFLAKE_PASSWORD").get_value(),
        account=EnvVar("SNOWFLAKE_ACCOUNT").get_value(),
        database=EnvVar("SNOWFLAKE_DATABASE").get_value(),
        schema=EnvVar("SNOWFLAKE_SCHEMA").get_value(),
        warehouse="compute_wh"
    )

    OANDA = OandaClient(
        api_key=EnvVar("OANDA_API_KEY").get_value(),
        account_id='001-001-10122498-001',
        is_demo=False
    )

    event = {
        'instrument': 'EUR_USD',
        'granularity': 'H1',
        'count': 2
    }

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
        endpoint=OANDA.base_url + f'/instruments/{instrument}/candles',
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
    {EnvVar("SNOWFLAKE_DATABASE").get_value()}.DATA
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
            'count': 4
            # 'from_date': '2025-05-01T00:00:00Z'
        }
        result = lambda_handler(test_event, None)

