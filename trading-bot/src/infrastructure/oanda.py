import requests

class OandaAPIAuthError(Exception):
  pass

class OandaEndpointError(Exception):
    pass

class OandaClient:
    def __init__(self, api_key, account_id: str=None, is_live: bool=False):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = (
            "https://api-fxtrade.oanda.com/v3" if is_live
            else "https://api-fxpractice.oanda.com/v3"
        )

        if account_id:
            self.base_url = f"{self.base_url}/accounts/{self.account_id}"

    # TODO: DECRYPT THE API KEY ON THE REQUEST
    def send_request(
        self,
        endpoint: str,
        method: str,
        params: dict=None,
        data=None
    ):
        response = requests.request(
            method=method,
            url=f'{self.base_url}/{endpoint}',
            params=params,
            json=data,
            headers={
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        if 'Insufficient authorization' in response.text:
            raise OandaAPIAuthError(response.text)
        elif 'Unrecognized endpoint' in response.text:
            raise OandaEndpointError(response.text)
        else:
            response.raise_for_status()

        return response


class PositionSizerService:
    def __init__(self, oanda_client: OandaClient):
        self.oanda = oanda_client

    # def size_position_for_instrument(
    #     self, instrument: str, sizing_type: str, sizing_value: float
    # ) -> int:
    #     account_balance = self.get_account_balance()
    #     conversion_rate = self.get_conversion_rate(instrument)
    #     return size_position(account_balance, instrument, sizing_type, sizing_value, conversion_rate)
    #
    # def get_account_balance(self) -> float:
    #     # Example endpoint: /accounts/{accountID}/summary
    #     response = self.oanda.send_request(
    #         endpoint=f"{self.oanda.base_url}/summary",
    #         method="GET"
    #     )
    #     return float(response.json()["account"]["balance"])
    #
    # def get_conversion_rate(self, instrument: str) -> float:
    #     # Example: get exchange rate for USD_CAD if instrument is USD_CAD
    #     # You may need to derive a conversion pair from the instrument name
    #     # and call /pricing or /instruments endpoint
    #     raise NotImplementedError("Add logic to fetch FX rate if needed")
