WITH

deduped_candles AS (

  SELECT
    *
  FROM {{ source('candle_data', 'hour1_renko_bricks') }}
  QUALIFY row_number() over (
      PARTITION BY instrument, candle_close_time
      ORDER BY
        candle_close_time DESC,
        brick_number DESC
  ) = 1

),

direction_shifter AS (

  SELECT
    *,
    brick_type != LAG(brick_type) OVER (
      PARTITION BY instrument
      ORDER BY candle_close_time ASC
    ) AS did_direction_shift,
  FROM deduped_candles

)

SELECT
  instrument,
  candle_open_time,
  candle_close_time,
  brick_type,
  did_direction_shift,
  streak_order,
  brick_number,

  SUM(CASE WHEN did_direction_shift THEN 1 ELSE 0 END)
    OVER (PARTITION BY instrument ORDER BY candle_close_time ASC) AS trend_group,

  open,
  high,
  low,
  close,
  brick_inserted_at,
FROM direction_shifter
ORDER BY candle_close_time DESC
