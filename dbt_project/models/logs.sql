WITH

source_data AS (

  SELECT * FROM {{ source('application_data', 'account_logs') }}

),

parse_data AS (

  SELECT
    transactions.value['accountID']::varchar as platform_id,
    transactions.value['id']::integer as transaction_id,
    transactions.value['batchID']::integer as transaction_batch_id,
    transactions.value['orderID']::integer as order_transaction_id,
    transactions.value['tradeOpened']['tradeID']::integer as entry_id,
    transactions.value['type']::varchar as transaction_type,

    COALESCE(
      transactions.value['reason']::varchar,
      transactions.value['fundingReason']::varchar
    ) as transaction_reason,

    transactions.value['instrument']::varchar as instrument,
    transactions.value['pl']::varchar as profit_loss,
    transactions.value['financing']::varchar as financing,
    transactions.value['amount']::float as funding_amount,
    transactions.value['accountBalance']::float as account_balance_after_transaction,
    transactions.value['tradeOpened']['units']::float as entry_units,
    transactions.value['tradeOpened']['price']::float as entry_price,
    transactions.value['tradeOpened']['initialMarginRequired']::float as entry_initial_margin_required,
    transactions.value['tradeOpened']['halfSpreadCost']::float as entry_half_spread_cost,
    transactions.value['tradeOpened']::variant as trade_json,


    transactions.value['clientExtensions']['id']::varchar as client_extension_id,
    transactions.value['clientExtensions']['tag']::varchar as client_extension_tag,
    transactions.value['requestID']::varchar as request_id,
    transactions.value['userID']::varchar as user_id,
    transactions.value['time']::timestamp as transaction_time,
    transactions.value::variant as raw_data,
    source_data.filename,
    source_data.file_last_modified
  FROM source_data,
    LATERAL FLATTEN(input => source_data.raw_data['transactions']) AS transactions
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY platform_id, transaction_id
    ORDER BY transaction_time DESC, file_last_modified DESC
  ) = 1

)

SELECT * FROM parse_data
