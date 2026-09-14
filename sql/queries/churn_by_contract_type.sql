-- ==============================================================================
-- Query: Churn Rate by Contract Type
-- Business Purpose:
--   Evaluates customer commitment levels (Month-to-month vs 1-Year vs 2-Year).
--   Demonstrates the revenue risk associated with flexible monthly terms vs
--   long-term contracts, informing contract incentive and discounting strategies.
-- ==============================================================================

SELECT
    Contract AS contract_type,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
    SUM(CASE WHEN Churn = 'No' THEN 1 ELSE 0 END) AS retained_customers,
    ROUND(
        100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(SUM(TotalCharges), 2) AS total_contract_revenue
FROM customers
GROUP BY Contract
ORDER BY churn_rate_pct DESC;
