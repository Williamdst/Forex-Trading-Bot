def size_position(
    account_balance: float,
    instrument: str,
    sizing_type: str,
    sizing_value: float,
    conversion_rate: float,
    direction: str
) -> int:
    instrument = instrument.upper()
    sizing_type = sizing_type.upper()
    direction = direction.upper()

    if direction not in ['LONG', 'SHORT']:
        raise ValueError("Direction must be either 'LONG' or 'SHORT'")

    if sizing_type == 'FIXED_PIP_SIZE':
        return fixed_pip_sizing(
            account_balance,
            instrument,
            sizing_value,
            conversion_rate,
            direction
        )
    else:
        raise ValueError(f'Unsupported sizing type: {sizing_type}')

def fixed_pip_sizing(
    account_balance: float,
    instrument: str,
    sizing_value: float,
    conversion_rate: float,
    direction: str
) -> int:
    pip_size_units = (
        account_balance * sizing_value * 100 if 'JPY' in instrument
        else account_balance * sizing_value * 10000
    )
    units = int(pip_size_units / conversion_rate)
    return units if direction == 'LONG' else -1 * units
