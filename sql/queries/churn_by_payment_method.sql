-- ==============================================================================
-- Query: Churn Rate by Payment Method
-- Business Purpose:
--   Compares churn rates across billing channels (Electronic Check, Mailed Check,
--   Bank Transfer, Credit Card). Identifies payment friction and helps design
--   campaigns to migrate users to automated recurring payments.
-- ==============================================================================

SELECT
    PaymentMethod AS payment_method,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
    SUM(CASE WHEN Churn = 'No' THEN 1 ELSE 0 END) AS retained_customers,
    ROUND(
        100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(SUM(TotalCharges), 2) AS total_revenue
FROM customers
GROUP BY PaymentMethod
ORDER BY churn_rate_pct DESC;
