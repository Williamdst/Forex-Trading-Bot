with

hour1_renko_bricks as (

  SELECT * FROM {{ ref('dim_oanda_hour1_renko_bricks_deduped') }}

),

dim_oanda_hour1_candles as (

  SELECT * FROM {{ ref('dim_oanda_hour1_forex_candles') }}

),

join_renko_to_ohlc as (

  SELECT
    ohlc.*,
    bricks.candle_close_time as brick_close_time,
    bricks.candle_open_time as brick_open_time,
    bricks.brick_type,
    bricks.open as brick_open,
    bricks.high as brick_high,
    bricks.low as brick_low,
    bricks.close as brick_close,
    bricks.streak_order,
    bricks.trend_group,
    bricks.did_direction_shift
  FROM dim_oanda_hour1_candles as ohlc
  LEFT JOIN hour1_renko_bricks as bricks
    ON ohlc.candle_open_time = bricks.candle_close_time
   AND ohlc.instrument = bricks.instrument

)

select * from join_renko_to_ohlc
order by candle_open_time desc
