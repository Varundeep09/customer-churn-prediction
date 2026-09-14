-- ==============================================================================
-- Query: Churn Rate for High-Risk Service Combination
-- Business Purpose:
--   Tests the hypothesis that customers with high-speed Fiber Optic internet who
--   LACK support/security add-ons (OnlineSecurity = 'No' AND TechSupport = 'No')
--   experience severe churn compared to all other customer configurations.
--   Directly informs bundle packaging and tech support onboarding workflows.
-- ==============================================================================

SELECT
    CASE
        WHEN InternetService = 'Fiber optic'
             AND OnlineSecurity = 'No'
             AND TechSupport = 'No'
        THEN 'High-Risk Combo (Fiber + No Security + No Support)'
        ELSE 'All Other Service Profiles'
    END AS service_cohort,
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
GROUP BY service_cohort
ORDER BY churn_rate_pct DESC;
