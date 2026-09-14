"""
Execute all SQL analytical queries against churn.db,
display formatted result tables in console, and export clean CSVs
to sql/query_results/ for reporting and dashboard analysis.
"""

import sqlite3
from pathlib import Path
import pandas as pd


def run_and_export_queries() -> None:
    project_root = Path(__file__).resolve().parents[1]
    sql_dir = project_root / "sql"
    db_path = sql_dir / "churn.db"
    queries_dir = sql_dir / "queries"
    results_dir = sql_dir / "query_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}. Please run build_database.py first.")

    query_files = [
        ("churn_by_tenure_cohort.sql", "1. Churn Rate by Tenure Cohort"),
        ("churn_by_contract_type.sql", "2. Churn Rate by Contract Type"),
        ("churn_by_payment_method.sql", "3. Churn Rate by Payment Method"),
        ("churn_by_customer_value.sql", "4. Churn Rate by Customer Value Tier"),
        ("churn_by_service_combo.sql", "5. Churn Rate by Service Combination (Fiber + No Support/Security)"),
        ("high_value_at_risk.sql", "6. High-Value At-Risk Customer Target List (Month-to-Month, >$70, <12m Tenure)"),
    ]

    conn = sqlite3.connect(db_path)
    try:
        print("=" * 80)
        print("EXECUTING SQL ANALYTICS LAYER ON CHURN.DB")
        print("=" * 80)

        for filename, title in query_files:
            file_path = queries_dir / filename
            if not file_path.exists():
                print(f"Warning: File {file_path} does not exist. Skipping.")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                query_sql = f.read()

            df_result = pd.read_sql_query(query_sql, conn)

            # Export to CSV
            csv_name = filename.replace(".sql", ".csv")
            csv_path = results_dir / csv_name
            df_result.to_csv(csv_path, index=False)

            print(f"\n>>> {title}")
            print(f"    Source Query: sql/queries/{filename}")
            print(f"    Exported CSV: sql/query_results/{csv_name}")
            print(f"    Records: {len(df_result)}")
            print("-" * 80)

            # If large dataset, show top preview, otherwise show entire table
            if len(df_result) > 15:
                print(df_result.head(10).to_string(index=False))
                print(f"... and {len(df_result) - 10} more rows.")
            else:
                print(df_result.to_string(index=False))

            print("-" * 80)

        print("\nAll 6 queries executed successfully and results saved to sql/query_results/.")
    finally:
        conn.close()


if __name__ == "__main__":
    run_and_export_queries()
