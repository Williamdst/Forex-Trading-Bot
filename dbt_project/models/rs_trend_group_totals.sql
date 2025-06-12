with

brick_num_assignment as (

select
  *,
  CASE WHEN did_direction_shift then 0 ELSE streak_order+1 END as bricks_made
from {{ ref('dim_oanda_hour1_renko_bricks_deduped') }}

),

trend_group_totals as (

select
  instrument,
  trend_group,
  sum(t.bricks_made) - 2 as total_bricks_made
from brick_num_assignment as t
group by instrument, trend_group

),

trend_group_pips_total AS (

  SELECT
    t.*,

    CASE
      WHEN t.instrument like '%JPY' then t.total_bricks_made * i.brick_size * 100
      ELSE t.total_bricks_made * i.brick_size * 10000
    END as total_pips_made

  FROM trend_group_totals AS t
  LEFT JOIN {{ source('application_data', 'instruments') }} AS i
    ON t.instrument = i.instrument

)


select * from trend_group_pips_total
ORDER BY instrument asc, trend_group ASC