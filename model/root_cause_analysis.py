"""
Root Cause Analysis for Customer Churn using Statistical Hypothesis Testing.

Why Statistical Testing Over Model Feature Importance?
-------------------------------------------------------
Tree-based feature importance (e.g. Random Forest Gini importance) can be biased
toward continuous variables with high cardinality, struggles with correlated features,
and doesn't provide a probabilistic confidence measure (p-value).

Statistical hypothesis testing provides:
1. Chi-Square Test of Independence (for Categorical features):
   - Measures whether the observed distribution of churn across categories differs
     significantly from what would be expected purely by random chance.
   - Null Hypothesis (H0): Churn is independent of the categorical feature.
   - P-value < 0.05 rejects H0, confirming a statistically significant relationship.

2. Point-Biserial Correlation (for Continuous/Numeric features vs Binary Target):
   - A specialized Pearson correlation measuring the linear relationship between a
     continuous variable (e.g., tenure, MonthlyCharges) and a binary variable (Churn 0/1).
   - Positive r: higher values increase likelihood of churn (e.g., higher monthly charges).
   - Negative r: higher values decrease likelihood of churn (e.g., longer tenure protects against churn).
   - P-value < 0.05 indicates the correlation is statistically significant.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, pointbiserialr


def generate_interpretation(feature: str, test_type: str, statistic: float, p_value: float, corr_sign: float = None) -> str:
    """Generate human-readable, plain-English summary of statistical test results."""
    sig_text = "statistically significant" if p_value < 0.05 else "not statistically significant"
    p_str = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.4f}"

    if test_type == "Chi-Square Test":
        if statistic > 500:
            strength = "an exceptionally strong"
        elif statistic > 100:
            strength = "a very strong"
        elif statistic > 20:
            strength = "a moderate"
        else:
            strength = "a weak"
        return f"{feature} has {strength}, {sig_text} association with churn ({p_str}, chi2 = {statistic:.2f})."
    else:
        direction = "effect increasing churn risk" if corr_sign > 0 else "protective effect against churn"
        if abs(statistic) >= 0.30:
            strength = "strong"
        elif abs(statistic) >= 0.15:
            strength = "moderate"
        else:
            strength = "weak"
        return f"Higher {feature} has a {strength} {direction} ({p_str}, r = {statistic:+.3f})."


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
    model_dir = project_root / "model"

    # 1. Load and clean dataset (replicate preprocess.py cleanup logic)
    df = pd.read_csv(data_path)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).copy()
    if "customerID" in df.columns:
        df = df.drop(columns=["customerID"])

    # Create binary numeric target for point-biserial correlation
    churn_numeric = df["Churn"].map({"Yes": 1, "No": 0})

    numeric_features = ["tenure", "MonthlyCharges", "TotalCharges"]
    categorical_features = [
        col for col in df.columns
        if col not in numeric_features and col != "Churn"
    ]

    findings = []

    # 2. Chi-Square Test of Independence for Categorical Features
    for feature in categorical_features:
        contingency_table = pd.crosstab(df[feature], df["Churn"])
        chi2_stat, p_val, dof, _ = chi2_contingency(contingency_table)

        # Calculate Cramer's V as standard effect size measure for Chi-Square
        n = contingency_table.sum().sum()
        min_dim = min(contingency_table.shape) - 1
        cramers_v = np.sqrt(chi2_stat / (n * min_dim)) if min_dim > 0 else 0.0

        interpretation = generate_interpretation(feature, "Chi-Square Test", chi2_stat, p_val)

        findings.append({
            "feature": feature,
            "feature_type": "Categorical",
            "test_used": "Chi-Square Test",
            "statistic_name": "Chi2 Stat",
            "statistic_value": round(float(chi2_stat), 4),
            "effect_size_name": "Cramér's V",
            "effect_size_value": round(float(cramers_v), 4),
            "p_value": float(p_val),
            "p_value_formatted": "< 0.0001" if p_val < 0.0001 else f"{p_val:.4f}",
            "is_significant": bool(p_val < 0.05),
            "degrees_of_freedom": int(dof),
            "interpretation": interpretation,
        })

    # 3. Point-Biserial Correlation for Numeric Features
    for feature in numeric_features:
        corr_stat, p_val = pointbiserialr(churn_numeric, df[feature])
        interpretation = generate_interpretation(
            feature, "Point-Biserial", corr_stat, p_val, corr_sign=corr_stat
        )

        findings.append({
            "feature": feature,
            "feature_type": "Numeric",
            "test_used": "Point-Biserial Corr",
            "statistic_name": "Correlation (r)",
            "statistic_value": round(float(corr_stat), 4),
            "effect_size_name": "|r|",
            "effect_size_value": round(float(abs(corr_stat)), 4),
            "p_value": float(p_val),
            "p_value_formatted": "< 0.0001" if p_val < 0.0001 else f"{p_val:.4f}",
            "is_significant": bool(p_val < 0.05),
            "degrees_of_freedom": len(df) - 2,
            "interpretation": interpretation,
        })

    # Sort all findings by statistical strength:
    # We rank by effect size / significance (p-value first, then effect size)
    findings_sorted = sorted(
        findings,
        key=lambda x: (x["p_value"], -x["effect_size_value"])
    )

    # 4. Print Ranked Summary Table
    print("=" * 115)
    print("ROOT CAUSE ANALYSIS: STATISTICAL DRIVERS OF CUSTOMER CHURN")
    print("=" * 115)
    header = f"{'Rank':<5} | {'Feature':<18} | {'Type':<12} | {'Test Used':<19} | {'Statistic':<12} | {'p-value':<10} | {'Effect Size':<12}"
    print(header)
    print("-" * 115)

    for rank, item in enumerate(findings_sorted, 1):
        stat_display = f"{item['statistic_value']:+.4f}" if item['feature_type'] == 'Numeric' else f"{item['statistic_value']:.2f}"
        effect_display = f"{item['effect_size_name']}={item['effect_size_value']:.3f}"
        p_display = item["p_value_formatted"]
        print(
            f"{rank:<5} | {item['feature']:<18} | {item['feature_type']:<12} | {item['test_used']:<19} | {stat_display:<12} | {p_display:<10} | {effect_display:<12}"
        )

    print("-" * 115)
    print("\nPLAIN-ENGLISH INTERPRETATIONS BY CATEGORY:\n")

    print("[TOP CATEGORICAL CHURN DRIVERS (Chi-Square Test)]")
    cat_items = [f for f in findings_sorted if f["feature_type"] == "Categorical"]
    for item in cat_items[:6]:
        print(f"  * {item['feature']}: {item['interpretation']}")

    print("\n[NUMERIC CHURN DRIVERS (Point-Biserial Correlation)]")
    num_items = [f for f in findings_sorted if f["feature_type"] == "Numeric"]
    for item in num_items:
        print(f"  * {item['feature']}: {item['interpretation']}")

    # 5. Save structured output to JSON
    output_path = model_dir / "root_cause_findings.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_title": "Telco Customer Churn Root Cause Analysis",
                "sample_size": len(df),
                "ranked_drivers": findings_sorted,
            },
            f,
            indent=2,
        )

    print(f"\nRoot cause findings successfully exported to: {output_path}")


if __name__ == "__main__":
    main()
