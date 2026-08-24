-- FlinkSQL DDL stubs for velocity windows (PLAN §9).
-- TODO: define source (Kafka), tumbling windows, and sink (Redis/RonDB).
CREATE TABLE transactions_src (
  transaction_id STRING,
  user_id STRING,
  amount_minor BIGINT,
  ts TIMESTAMP(3) METADATA FROM 'timestamp'
) WITH ('connector' = 'kafka', 'topic' = 'transactions', 'format' = 'json');
