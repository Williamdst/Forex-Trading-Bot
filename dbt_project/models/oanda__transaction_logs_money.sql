WITH

transaction_logs AS (

  SELECT * FROM {{ ref('oanda__transaction_logs') }}

),

full_trade_info_join AS (

    SELECT

      logs.platform_id,
      logs.transaction_id,
      logs.transaction_batch_id,
      logs.order_transaction_id,
      logs.trade_open_id,
      close_trade.trade_close_id,
      logs.transaction_reason as trade_open_reason,
      close_trade.transaction_reason as trade_close_reason,
      logs.instrument,
      close_trade.profit_loss,
      logs.financing,
      logs.funding_amount,
      logs.entry_units,
      logs.trade_price as trade_open_price,
      close_trade.trade_price as trade_close_price,
      logs.entry_initial_margin_required as initial_margin_required,
      logs.entry_half_spread_cost as half_spread_cost,
      client_order.client_extension_id,
      client_order.client_extension_tag,
      logs.transaction_time as trade_open_time,
      close_trade.transaction_time as trade_close_time

    FROM transaction_logs as logs
    left join transaction_logs as client_order
      on logs.order_transaction_id = client_order.transaction_id
      and logs.platform_id = client_order.platform_id
    left join transaction_logs as close_trade
      on logs.trade_open_id = close_trade.trade_close_id
      and logs.platform_id = close_trade.platform_id
)

select * from full_trade_info_join
    where platform_id = '101-001-26574809-001'