-- ==============================================================================
-- Query: High-Value At-Risk Customer Target List
-- Business Purpose:
--   Extracts individual accounts presenting the highest immediate revenue risk:
--     1. High Monthly Charges (MonthlyCharges > $70)
--     2. No long-term lock-in (Contract = 'Month-to-month')
--     3. Early lifecycle stage (tenure < 12 months)
--   This actionable list serves as the primary input for customer success &
--   proactive retention discount/contract upgrade campaigns.
-- ==============================================================================

SELECT
    customerID,
    gender,
    SeniorCitizen,
    tenure,
    Contract,
    PaymentMethod,
    InternetService,
    TechSupport,
    OnlineSecurity,
    MonthlyCharges,
    TotalCharges,
    Churn
FROM customers
WHERE MonthlyCharges > 70.0
  AND Contract = 'Month-to-month'
  AND tenure < 12
ORDER BY MonthlyCharges DESC, tenure ASC;
