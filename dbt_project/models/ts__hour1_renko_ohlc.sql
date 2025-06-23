with

hour1_renko_bricks as (

  SELECT * FROM {{ ref('oanda__hour1_renko_bricks_deduped') }}

),

dim_oanda_hour1_candles as (

  SELECT * FROM {{ ref('oanda__hour1_forex_candles') }}

),

join_renko_to_ohlc as (

  SELECT

    ohlc.*,
    bricks.candle_open_time as brick_open_time,
    bricks.candle_close_time as brick_close_time,
    bricks.brick_type,
    bricks.open as brick_open,
    bricks.high as brick_high,
    bricks.low as brick_low,
    bricks.close as brick_close,
    bricks.streak_order,
    bricks.trend_group,
    bricks.brick_number,
    bricks.did_direction_shift

  FROM dim_oanda_hour1_candles as ohlc

  {%- if target.name == 'dev' %}
  INNER JOIN hour1_renko_bricks as bricks
  {% else %}
  LEFT JOIN hour1_renko_bricks as bricks
  {% endif -%}

    ON ohlc.candle_close_time = bricks.candle_close_time
   AND ohlc.instrument = bricks.instrument

),

exeuction_flagging AS (

  SELECT

    *,
    lag(brick_type) over (
      partition by instrument
      order by candle_open_time asc
    ) as trade_execution_type,

    lag(did_direction_shift) over (
      partition by instrument
      order by candle_open_time asc
    ) as execute_trade_flag,

    lag(brick_number) over (
      partition by instrument
      order by candle_open_time asc
    ) as execute_brick_number,

    lag(trend_group) over (
      partition by instrument
      order by candle_open_time asc
    ) as execute_trend_group

  FROM join_renko_to_ohlc

)

SELECT * FROM exeuction_flagging
ORDER BY candle_open_time DESC
