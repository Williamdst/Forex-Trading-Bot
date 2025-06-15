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
