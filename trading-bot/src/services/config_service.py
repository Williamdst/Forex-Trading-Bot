from infrastructure.snowflake import SnowflakeClient

class ConfigProvider:
    def __init__(self, snowflake_client: SnowflakeClient):
        self.snowflake_client = snowflake_client

    def get_account_credentials(self, account_id: str) -> dict:
        result = self.snowflake_client.run_query(
            query=(f"""
                SELECT
                  accounts.platform_id,
                  accounts.is_live_account,
                  api.api_key
                FROM PRODUCTION.APPLICATION.ACCOUNTS as accounts
                LEFT JOIN PRODUCTION.APPLICATION.API_KEYS as api
                    ON accounts.api_key_id = api.api_key_id
                WHERE accounts.account_id = '{account_id}'
            """
            ),
            use_dict_cursor=True
        )
        if not result:
            raise ValueError("Oanda API credentials not found")
        return result[0]

    def get_account_instrument_config(
        self,
        account_id: str,
        instrument: str
    ) -> dict:
        result = self.snowflake_client.run_query(
            query=(f"""
                SELECT
                  aic.position_sizing_type,
                  aic.position_sizing_value
                FROM PRODUCTION.APPLICATION.INSTRUMENTS as i
                LEFT JOIN PRODUCTION.APPLICATION.account_instruments_config as aic
                  ON i.instrument_id = aic.instrument_id
                WHERE i.instrument = '{instrument}'
                  AND aic.account_id = '{account_id}'
                  AND aic.is_active
            """),
            use_dict_cursor=True
        )
        if not result:
            raise ValueError(f"Instrument configuration for {instrument} not found")
        return result[0]
