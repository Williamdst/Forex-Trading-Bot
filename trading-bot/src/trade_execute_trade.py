import os
from dotenv import load_dotenv

from infrastructure.oanda import OandaClient
from infrastructure.snowflake import SnowflakeClient

from services.sizer_service import PositionSizer
from services.config_service import ConfigProvider
from services.trade_service import TradeManager

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
    instrument = event['INSTRUMENT']
    direction = event['DIRECTION']
    print(f'running for instrument {instrument} for account {account_id} in direction {direction}')

    config_service = ConfigProvider(SNOWFLAKE)
    oanda_credentials = config_service.get_account_credentials(
        account_id=account_id
    )
    OANDA = OandaClient(
        account_id=oanda_credentials['PLATFORM_ID'],
        api_key=oanda_credentials['API_KEY'],
        is_live=oanda_credentials['IS_LIVE_ACCOUNT']
    )

    position_service = PositionSizer(OANDA)
    instrument_config = config_service.get_account_instrument_config(
        account_id=account_id,
        instrument=instrument
    )
    trade_size_units = position_service.size_position_for_instrument(
        instrument=instrument,
        sizing_type=instrument_config['POSITION_SIZING_TYPE'],
        sizing_value=float(instrument_config['POSITION_SIZING_VALUE']),
        direction=direction
    )

    trade_service = TradeManager(OANDA)
    trade_service.close_position_for_instrument(instrument=instrument)
    trade_service.open_market_position_for_instrument(
        instrument=instrument,
        trade_size_units=trade_size_units
    )

    return None


if __name__ == "__main__":
    for instrument in [
        'EUR_USD', 'USD_CAD', 'GBP_USD', 'USD_CHF',
        'AUD_USD', 'NZD_USD', 'USD_JPY'
    ]:
        test_event = {
            'ACCOUNT_ID': 1,
            'INSTRUMENT': instrument,
            'DIRECTION': 'LONG',
        }
        lambda_handler(test_event, None)
