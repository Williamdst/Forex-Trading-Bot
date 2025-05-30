import pandas as pd

def generate_renko_bricks(df: pd.DataFrame, brick_config: dict):
    # The function recreates the entire renko dataset given the OHLC candles
    renko_list = []

    brick_size = brick_config['brick_size']
    previous_candle_stats = {
        'candle_open_time': None,
        'candle_close_time': None,
        'open': brick_config['artificial_brick_open'],
        'close': brick_config['artificial_brick_close'],
        'brick_type': brick_config['brick_type'],
        'streak_order': 0
    }

    for index, row in df.iterrows():
        current_candle_close_time = row['candle_close_time']
        current_close = row['mid_close']

        # Long Renko Candles
        # The if statement is based on what type of renko candle is the
        # previous one in the series. The strategy for determining the next
        # renko candles is the same, but the logic is reversed along with some
        # of the values that need to be used.
        if previous_candle_stats['brick_type'] == 'long':
            # Set the values that determine the thresholds for the next candle
            long_contd = previous_candle_stats['close'] + brick_size
            short_rvrsl = previous_candle_stats['open'] - brick_size

            # This if statement determines which threshold was passed.
            # The threshold to continue the current long renko candle or reverse
            if current_close >= long_contd:
                # Calculate the number of renko candles that need to be
                # created based on how many "brick sizes" were passed
                brick_moves = int((current_close - previous_candle_stats['close']) / brick_size)

                # For every candle
                for i in range(brick_moves):
                    current_candle_stats = {
                        'candle_open_time': previous_candle_stats['candle_close_time'],
                        'candle_close_time': current_candle_close_time,
                        'open': previous_candle_stats['close'],
                        'close': previous_candle_stats['close'] + brick_size,
                        'brick_type': 'long',
                        'streak_order': i
                    }

                    # We want the logic of incrementing the close price by the
                    # brick size. But in the case when there are multiple brick
                    # moves, we want to ensure that the opening time for all the
                    # subsequent candles is the same as the first one.
                    if i > 0:
                        current_candle_stats['candle_open_time'] = previous_candle_stats['candle_open_time']

                    # Add the current renko candle to the list
                    # and update the previous candle with the current candle
                    # for the next iteration
                    renko_list.append(current_candle_stats)
                    previous_candle_stats = current_candle_stats

            elif current_close <= short_rvrsl:
                brick_moves = int((previous_candle_stats['open'] - current_close) / brick_size)

                for i in range(brick_moves):
                    current_candle_stats = {
                        'candle_open_time': previous_candle_stats['candle_close_time'],
                        'candle_close_time': current_candle_close_time,
                        'open': previous_candle_stats['open'],
                        'close': previous_candle_stats['open'] - brick_size,
                        'brick_type': 'short',
                        'streak_order': i
                    }

                    if i > 0:
                        current_candle_stats = {
                            'candle_open_time': previous_candle_stats['candle_open_time'],
                            'candle_close_time': current_candle_close_time,
                            'open': previous_candle_stats['close'],
                            'close': previous_candle_stats['close'] - brick_size,
                            'brick_type': 'short',
                            'streak_order': i
                        }

                    renko_list.append(current_candle_stats)
                    previous_candle_stats = current_candle_stats

        # Short Renko Candles
        elif previous_candle_stats['brick_type'] == 'short':
            short_contd = previous_candle_stats['close'] - brick_size
            long_rvrsl = previous_candle_stats['open'] + brick_size

            if current_close <= short_contd:
                brick_moves = int((previous_candle_stats['close'] - current_close) / brick_size)

                for i in range(brick_moves):
                    current_candle_stats = {
                        'candle_open_time': previous_candle_stats['candle_close_time'],
                        'candle_close_time': current_candle_close_time,
                        'open': previous_candle_stats['close'],
                        'close': previous_candle_stats['close'] - brick_size,
                        'brick_type': 'short',
                        'streak_order': i
                    }

                    if i > 0:
                        current_candle_stats['candle_open_time'] = previous_candle_stats['candle_open_time']

                    renko_list.append(current_candle_stats)
                    previous_candle_stats = current_candle_stats

            elif current_close >= long_rvrsl:
                brick_moves = int((current_close - previous_candle_stats['open']) / brick_size)

                for i in range(brick_moves):
                    current_candle_stats = {
                        'candle_open_time': previous_candle_stats['candle_close_time'],
                        'candle_close_time': current_candle_close_time,
                        'open': previous_candle_stats['open'],
                        'close': previous_candle_stats['open'] + brick_size,
                        'brick_type': 'long',
                        'streak_order': i
                    }

                    if i > 0:
                        current_candle_stats = {
                            'candle_open_time': previous_candle_stats['candle_open_time'],
                            'candle_close_time': current_candle_close_time,
                            'open': previous_candle_stats['close'],
                            'close': previous_candle_stats['close'] + brick_size,
                            'brick_type': 'long',
                            'streak_order': i
                        }

                    renko_list.append(current_candle_stats)
                    previous_candle_stats = current_candle_stats

    renko_bricks = pd.DataFrame.from_dict(renko_list)
    # renko_bricks.sort_values(['candle_open_time', 'streak_order'], ascending=[True, True], inplace=True)
    renko_bricks['high'] = renko_bricks[['open', 'close']].max(axis=1)
    renko_bricks['low'] = renko_bricks[['open', 'close']].min(axis=1)
    return renko_bricks