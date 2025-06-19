from infrastructure.oanda import OandaClient

class TradeManager:
    def __init__(self, oanda_client: OandaClient):
        self.oanda = oanda_client

    def close_position_for_instrument(self, instrument: str) -> None:
        response = self.oanda.send_request(
            method='GET',
            endpoint=f'positions'
        ).json()

        for position in response['positions']:
            if position['instrument'] == instrument:
                long_positions = int(position['long']['units'])
                short_positions = int(position['short']['units'])

                if long_positions != 0:
                    self.oanda.send_request(
                        method='PUT',
                        endpoint=f'positions/{instrument}/close',
                        data={'longUnits': 'ALL'}
                    )

                if short_positions != 0:
                    self.oanda.send_request(
                        method='PUT',
                        endpoint=f'positions/{instrument}/close',
                        data={'shortUnits': 'ALL'}
                    )
            else:
                continue

        return None

    def open_market_position_for_instrument(
        self,
        instrument: str,
        trade_size_units: int
    ) -> None:
        self.oanda.send_request(
            method='POST',
            endpoint='orders',
            data={
                'order': {
                    'type': 'MARKET',
                    'timeInForce': 'FOK',
                    'units': trade_size_units,
                    'instrument': instrument
                }
            }
        ).json()