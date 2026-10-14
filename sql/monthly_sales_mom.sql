-- Query 2: Monthly Sales Performance with Month-over-Month (MoM) Deviation
-- Demonstrates window functions: LAG() over monthly division collection
WITH monthly_summary AS (
    SELECT 
        month,
        SUM(COALESCE(collected_amount, 0)) AS total_collected,
        SUM(COALESCE(expected_amount, 0)) AS total_expected
    FROM division_monthly
    WHERE category = 'token_booking'
    GROUP BY month
)
SELECT 
    month,
    total_expected,
    total_collected,
    LAG(total_collected, 1) OVER (ORDER BY month) AS previous_month_collected,
    (total_collected - LAG(total_collected, 1) OVER (ORDER BY month)) AS mom_deviation,
    ROUND(
        CAST(
            CASE 
                WHEN LAG(total_collected, 1) OVER (ORDER BY month) IS NULL OR LAG(total_collected, 1) OVER (ORDER BY month) = 0 THEN 0
                ELSE ((total_collected - LAG(total_collected, 1) OVER (ORDER BY month)) / LAG(total_collected, 1) OVER (ORDER BY month)) * 100.0
            END AS numeric
        ), 2
    ) AS mom_growth_pct
FROM monthly_summary
ORDER BY month
LIMIT :limit_val OFFSET :offset_val;
