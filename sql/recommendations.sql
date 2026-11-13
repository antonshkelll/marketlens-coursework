-- Bind: cutoff seconds UTC, user_id, min_pair. sqrt is registered by Python.
WITH h AS MATERIALIZED (SELECT * FROM order_product WHERE ordered_at<:cutoff),
pop AS(SELECT product_id,COUNT(*) frequency FROM h GROUP BY product_id),
seen AS(SELECT DISTINCT product_id FROM h WHERE user_id=:user_id),
pairs AS(SELECT a.product_id source,b.product_id candidate,COUNT(*) n FROM h a JOIN h b ON a.order_id=b.order_id AND a.product_id<>b.product_id GROUP BY a.product_id,b.product_id),
scores AS(SELECT q.candidate product_id,SUM(1.0*q.n/sqrt(p.frequency*f.frequency)) score FROM pairs q JOIN seen s ON s.product_id=q.source JOIN pop p ON p.product_id=q.source JOIN pop f ON f.product_id=q.candidate WHERE q.n>=:min_pair GROUP BY q.candidate)
SELECT p.product_id,COALESCE(s.score,pop.frequency,0) score,CASE WHEN s.score IS NULL THEN 'popularity' ELSE 'cooccurrence' END reason
FROM product p LEFT JOIN scores s USING(product_id) LEFT JOIN pop USING(product_id)
WHERE NOT EXISTS(SELECT 1 FROM seen WHERE seen.product_id=p.product_id)
ORDER BY (s.score IS NOT NULL) DESC,COALESCE(s.score,pop.frequency,0) DESC,p.product_id LIMIT 10;
