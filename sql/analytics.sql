-- One row per session/product; strict sequence, purchase from confirmed orders.
CREATE VIEW funnel AS
WITH views AS(SELECT session_id,product_id,MIN(occurred_at) view_at FROM event WHERE event_type_id=1 GROUP BY session_id,product_id),
carts AS(SELECT v.*,MIN(e.occurred_at) cart_at FROM views v LEFT JOIN event e ON e.session_id=v.session_id AND e.product_id=v.product_id AND e.event_type_id=2 AND e.occurred_at>v.view_at GROUP BY v.session_id,v.product_id),
buys AS(SELECT c.*,MIN(o.ordered_at) buy_at FROM carts c LEFT JOIN order_product o ON o.session_id=c.session_id AND o.product_id=c.product_id AND o.ordered_at>c.cart_at GROUP BY c.session_id,c.product_id)
SELECT * FROM buys;
CREATE VIEW session_activity AS SELECT s.session_id,s.user_id,s.started_at,COUNT(e.event_id) depth,COALESCE(MAX(e.occurred_at)-MIN(e.occurred_at),0) duration FROM user_session s LEFT JOIN event e USING(session_id) GROUP BY s.session_id;
