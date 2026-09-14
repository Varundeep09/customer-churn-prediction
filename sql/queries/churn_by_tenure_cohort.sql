-- ==============================================================================
-- Query: Churn Rate by Customer Tenure Cohort
-- Business Purpose:
--   Examines churn trends across customer lifecycle stages (0-12m, 13-24m, 25-48m,
--   49-60m, 61-72m). Helps identify whether early customer onboarding or long-term
--   loyalty retention requires the most urgent attention.
-- ==============================================================================

SELECT
    CASE
        WHEN tenure BETWEEN 0 AND 12 THEN '0-12 Months'
        WHEN tenure BETWEEN 13 AND 24 THEN '13-24 Months'
        WHEN tenure BETWEEN 25 AND 48 THEN '25-48 Months'
        WHEN tenure BETWEEN 49 AND 60 THEN '49-60 Months'
        ELSE '61-72 Months'
    END AS tenure_cohort,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
    SUM(CASE WHEN Churn = 'No' THEN 1 ELSE 0 END) AS retained_customers,
    ROUND(
        100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(SUM(TotalCharges), 2) AS total_cohort_revenue
FROM customers
GROUP BY tenure_cohort
ORDER BY
    CASE tenure_cohort
        WHEN '0-12 Months' THEN 1
        WHEN '13-24 Months' THEN 2
        WHEN '25-48 Months' THEN 3
        WHEN '49-60 Months' THEN 4
        ELSE 5
    END;
