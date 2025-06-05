import requests

class OandaAPIAuthError(Exception):
  pass

class OandaEndpointError(Exception):
    pass

class OandaClient:
    def __init__(self, api_key, is_demo=True, account_id=None):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = (
            "https://api-fxpractice.oanda.com/v3" if is_demo
            else "https://api-fxtrade.oanda.com/v3"
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        if account_id:
            self.base_url = f"{self.base_url}/accounts/{self.account_id}"

    def send_request(self, endpoint: str, method: str, params=None, data=None):
        response = requests.request(
            method,
            url=endpoint,
            headers=self.headers,
            params=params,
            json=data
        )

        if 'Insufficient authorization' in response.text:
            raise OandaAPIAuthError(response.text)
        elif 'Unrecognized endpoint' in response.text:
            raise OandaEndpointError(response.text)
        else:
            response.raise_for_status()

        return response