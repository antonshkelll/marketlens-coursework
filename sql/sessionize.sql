-- raw_event: staging table with stable event identifiers.
CREATE TEMP VIEW numbered_raw AS
WITH lagged AS (
  SELECT *, LAG(occurred_at) OVER (
    PARTITION BY user_id ORDER BY occurred_at, event_id
  ) AS previous_at
  FROM raw_event
), bounded AS (
  SELECT *, CASE
    WHEN previous_at IS NULL OR occurred_at - previous_at > 1800
    THEN 1 ELSE 0 END AS new_session
  FROM lagged
)
SELECT *, SUM(new_session) OVER (
  PARTITION BY user_id ORDER BY occurred_at, event_id
  ROWS UNBOUNDED PRECEDING
) AS session_no
FROM bounded;

CREATE TEMP TABLE session_map AS
SELECT ROW_NUMBER() OVER (
  ORDER BY user_id, session_no
) AS session_id, user_id, session_no, MIN(occurred_at) AS started_at
FROM numbered_raw
GROUP BY user_id, session_no;

INSERT INTO user_session
SELECT session_id, user_id, started_at FROM session_map;

INSERT INTO event (
  event_id, session_id, event_type_id, product_id, occurred_at
)
SELECT e.event_id, s.session_id, e.event_type_id,
       e.product_id, e.occurred_at
FROM numbered_raw e JOIN session_map s USING (user_id, session_no);
