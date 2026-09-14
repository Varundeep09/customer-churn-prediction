-- ==============================================================================
-- Query: Churn Rate by Customer Value Tier (MonthlyCharges)
-- Business Purpose:
--   Segments customer base into spend tiers:
--     - Low Value: < $35/mo (typically voice-only / basic plans)
--     - Medium Value: $35 - $70/mo (standard bundles)
--     - High Value: > $70/mo (premium multi-service / fiber bundles)
--   Reveals if top-spending customers are leaving at disproportionate rates.
-- ==============================================================================

SELECT
    CASE
        WHEN MonthlyCharges < 35.0 THEN 'Low Value (<$35)'
        WHEN MonthlyCharges BETWEEN 35.0 AND 70.0 THEN 'Medium Value ($35-$70)'
        ELSE 'High Value (>$70)'
    END AS value_tier,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
    SUM(CASE WHEN Churn = 'No' THEN 1 ELSE 0 END) AS retained_customers,
    ROUND(
        100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(SUM(MonthlyCharges), 2) AS total_monthly_revenue_at_stake
FROM customers
GROUP BY value_tier
ORDER BY
    CASE value_tier
        WHEN 'High Value (>$70)' THEN 1
        WHEN 'Medium Value ($35-$70)' THEN 2
        ELSE 3
    END;
