-- ============================================
-- Sales & Operations Command Center - Queries
-- ============================================

-- =====================
-- 1. Revenue KPIs
-- =====================
-- Monthly revenue, order count, avg order value, and MoM growth
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::DATE  AS month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue,
        COUNT(DISTINCT o.order_id)                AS order_count
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY 1
)
SELECT
    month,
    revenue,
    order_count,
    ROUND(revenue / NULLIF(order_count, 0), 2)    AS avg_order_value,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100
    , 1)                                           AS mom_growth_pct
FROM monthly
ORDER BY month;


-- =====================
-- 2. Sales by Region
-- =====================
SELECT
    r.region_name,
    r.city,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN customers c    ON c.customer_id = o.customer_id
JOIN regions r      ON r.region_id = c.region_id
WHERE o.status = 'Completed'
GROUP BY r.region_name, r.city
ORDER BY revenue DESC;


-- =====================
-- 3. Product Performance
-- =====================
-- Top products by revenue with profit margin
SELECT
    p.product_name,
    cat.category_name,
    SUM(oi.quantity)                                            AS units_sold,
    SUM(oi.quantity * oi.unit_price * (1 - oi.discount))       AS revenue,
    SUM(oi.quantity * (oi.unit_price * (1 - oi.discount) - p.unit_cost)) AS profit,
    ROUND(
        SUM(oi.quantity * (oi.unit_price * (1 - oi.discount) - p.unit_cost))
        / NULLIF(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 0) * 100
    , 1)                                                        AS margin_pct
FROM order_items oi
JOIN products p    ON p.product_id = oi.product_id
JOIN categories cat ON cat.category_id = p.category_id
JOIN orders o      ON o.order_id = oi.order_id
WHERE o.status = 'Completed'
GROUP BY p.product_name, cat.category_name
ORDER BY revenue DESC
LIMIT 15;


-- =====================
-- 4. Customer RFM Segmentation
-- =====================
WITH rfm_raw AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.segment,
        MAX(o.order_date)                   AS last_order,
        COUNT(DISTINCT o.order_id)          AS frequency,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS monetary
    FROM customers c
    JOIN orders o       ON o.customer_id = c.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY c.customer_id, customer_name, c.segment
),
rfm_scored AS (
    SELECT *,
        NTILE(4) OVER (ORDER BY last_order DESC)  AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)    AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)     AS m_score
    FROM rfm_raw
)
SELECT *,
    CASE
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champion'
        WHEN r_score >= 3 AND f_score >= 2                  THEN 'Loyal'
        WHEN r_score >= 3 AND f_score = 1                   THEN 'New Customer'
        WHEN r_score = 2  AND f_score >= 2                  THEN 'At Risk'
        ELSE 'Needs Attention'
    END AS rfm_segment
FROM rfm_scored
ORDER BY monetary DESC;


-- =====================
-- 5. Inventory Health
-- =====================
SELECT
    p.product_name,
    cat.category_name,
    p.stock_qty,
    COALESCE(sold.units_sold_30d, 0)  AS units_sold_30d,
    CASE
        WHEN COALESCE(sold.units_sold_30d, 0) = 0 THEN NULL
        ELSE ROUND(p.stock_qty::NUMERIC / sold.units_sold_30d, 1)
    END                                AS days_of_stock,
    CASE
        WHEN p.stock_qty <= 10 THEN 'CRITICAL'
        WHEN p.stock_qty <= 50 THEN 'LOW'
        ELSE 'OK'
    END                                AS stock_status
FROM products p
JOIN categories cat ON cat.category_id = p.category_id
LEFT JOIN (
    SELECT oi.product_id, SUM(oi.quantity) AS units_sold_30d
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.status = 'Completed'
      AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY oi.product_id
) sold ON sold.product_id = p.product_id
ORDER BY days_of_stock ASC NULLS LAST;


-- =====================
-- 6. Sales Funnel (by channel)
-- =====================
SELECT
    channel,
    COUNT(*) FILTER (WHERE status IN ('Completed','Pending','Cancelled')) AS total_orders,
    COUNT(*) FILTER (WHERE status IN ('Completed','Pending'))            AS not_cancelled,
    COUNT(*) FILTER (WHERE status = 'Completed')                         AS completed,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'Completed')::NUMERIC
        / NULLIF(COUNT(*), 0) * 100
    , 1)                                                                  AS conversion_pct
FROM orders
GROUP BY channel
ORDER BY conversion_pct DESC;


-- =====================
-- 7. Employee Leaderboard
-- =====================
SELECT
    e.full_name,
    e.role,
    r.city,
    e.quota,
    COALESCE(s.revenue, 0)                                   AS revenue,
    ROUND(COALESCE(s.revenue, 0) / NULLIF(e.quota, 0) * 100, 1) AS quota_attainment_pct,
    COALESCE(s.deals, 0)                                     AS deals_closed
FROM employees e
JOIN regions r ON r.region_id = e.region_id
LEFT JOIN (
    SELECT
        o.employee_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue,
        COUNT(DISTINCT o.order_id) AS deals
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY o.employee_id
) s ON s.employee_id = e.employee_id
ORDER BY quota_attainment_pct DESC;


-- =====================
-- 8. Cohort Retention
-- =====================
WITH first_purchase AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date))::DATE AS cohort_month
    FROM orders WHERE status = 'Completed'
    GROUP BY customer_id
),
monthly_activity AS (
    SELECT DISTINCT
        o.customer_id,
        DATE_TRUNC('month', o.order_date)::DATE AS activity_month
    FROM orders o WHERE o.status = 'Completed'
)
SELECT
    fp.cohort_month,
    (DATE_PART('year', ma.activity_month) - DATE_PART('year', fp.cohort_month)) * 12
        + DATE_PART('month', ma.activity_month) - DATE_PART('month', fp.cohort_month)
        AS months_since_first,
    COUNT(DISTINCT ma.customer_id) AS active_customers
FROM first_purchase fp
JOIN monthly_activity ma ON ma.customer_id = fp.customer_id
GROUP BY fp.cohort_month, months_since_first
ORDER BY fp.cohort_month, months_since_first;


-- =====================
-- 9. Returns Analysis
-- =====================
SELECT
    cat.category_name,
    ret.reason,
    COUNT(*)                          AS return_count,
    SUM(oi.quantity * oi.unit_price)  AS returned_value
FROM returns ret
JOIN order_items oi ON oi.item_id = ret.item_id
JOIN products p     ON p.product_id = oi.product_id
JOIN categories cat ON cat.category_id = p.category_id
GROUP BY cat.category_name, ret.reason
ORDER BY return_count DESC;
