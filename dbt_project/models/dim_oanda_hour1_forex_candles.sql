WITH

deduped_candles AS (

  SELECT
    *,
    DATEADD(HOUR, 1, candle_open_time) as candle_close_time
  FROM {{ source('candle_data', 'oanda_hour1_forex_candles') }}
  QUALIFY row_number() over (
      PARTITION BY instrument, candle_open_time
      ORDER BY
        is_candle_complete DESC,
        volume DESC
  ) = 1

)

SELECT
  instrument,
  granularity,
  candle_open_time,
  candle_close_time,
  is_candle_complete,
  ask_open,
  ask_high,
  ask_low,
  ask_close,
  bid_open,
  bid_high,
  bid_low,
  bid_close,
  mid_open,
  mid_high,
  mid_low,
  mid_close,
  ROW_NUMBER() OVER(PARTITION BY instrument ORDER BY candle_open_time ASC) as candle_number
FROM deduped_candles
ORDER BY instrument, candle_open_time DESC