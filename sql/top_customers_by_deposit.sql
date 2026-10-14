-- Query 3: Top Customers by Cumulative Deposit
-- Parameterized query retrieving top depositing clients from July sales transactions
SELECT 
    client_id,
    client_name,
    division,
    sales_officer,
    sales_price,
    total_deposit,
    dues,
    booking_status
FROM sales_july
WHERE total_deposit IS NOT NULL
ORDER BY total_deposit DESC
LIMIT :limit_val OFFSET :offset_val;
