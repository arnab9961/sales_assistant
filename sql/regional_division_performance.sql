-- Query 4: Regional / Division Performance Analysis
-- Compares revenue generation, discount depth, and dues exposure across company divisions
SELECT 
    division,
    COUNT(*) AS total_deals,
    SUM(COALESCE(original_price, 0)) AS total_original_value,
    SUM(COALESCE(discount_amount, 0)) AS total_discount_given,
    ROUND(CAST(AVG(COALESCE(discount_pct, 0)) AS numeric), 2) AS avg_discount_pct,
    SUM(COALESCE(sales_price, 0)) AS total_sales_price,
    SUM(COALESCE(total_deposit, 0)) AS total_collected_deposit,
    SUM(COALESCE(dues, 0)) AS total_outstanding_dues
FROM sales_july
GROUP BY division
ORDER BY total_collected_deposit DESC
LIMIT :limit_val OFFSET :offset_val;
