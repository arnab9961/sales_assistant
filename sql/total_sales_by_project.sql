-- Query 1: Total Sales by Project and Category
-- Aggregates project performance across non-overlapping project records
SELECT 
    project_name,
    SUM(COALESCE(clients_qty, 0)) AS total_clients,
    SUM(COALESCE(share_qty, 0)) AS total_shares,
    SUM(COALESCE(sale_value, 0)) AS total_sale_value,
    SUM(COALESCE(only_sep_collected, 0)) AS total_collected_sep,
    ROUND(CAST(AVG(COALESCE(avg_sale_value, 0)) AS numeric), 2) AS avg_sale_value
FROM projects_sep
WHERE table_source = 'summary_non_overlapping'
GROUP BY project_name
ORDER BY total_collected_sep DESC
LIMIT :limit_val OFFSET :offset_val;
