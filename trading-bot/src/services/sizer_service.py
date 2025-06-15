from infrastructure.oanda import OandaClient
from domain.position_sizers import size_position

class PositionSizer:
    def __init__(self, oanda_client: OandaClient):
        self.oanda = oanda_client

    def size_position_for_instrument(
        self,
        instrument: str,
        sizing_type: str,
        sizing_value: float,
        direction: str
    ) -> int:
        account_balance = self.get_account_balance()
        conversion_rate = self.get_conversion_rate(instrument)
        return size_position(
            account_balance=account_balance,
            instrument=instrument,
            sizing_type=sizing_type,
            sizing_value=sizing_value,
            conversion_rate=conversion_rate,
            direction=direction
        )

    def get_account_balance(self) -> float:
        response = self.oanda.send_request(endpoint='summary', method="GET")
        return float(response.json()["account"]["balance"])

    def get_conversion_rate(self, instrument: str) -> float:
        response = self.oanda.send_request(
            method='GET',
            endpoint='pricing',
            params={'instruments': instrument}
        ).json()

        p_units = float(
            response['prices'][0]['quoteHomeConversionFactors']['positiveUnits']
        )
        n_units = float(
            response['prices'][0]['quoteHomeConversionFactors']['negativeUnits']
        )
        return (p_units + n_units) / 2
