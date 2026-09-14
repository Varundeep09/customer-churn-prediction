"""
Build SQLite Database for Customer Churn Analytics.
Loads raw Telco churn dataset, cleans missing TotalCharges values,
and persists cleaned records into a SQLite database table `customers`.
"""

import sqlite3
from pathlib import Path
import pandas as pd


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
    sql_dir = project_root / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    db_path = sql_dir / "churn.db"

    print(f"Reading raw dataset from: {data_path}")
    df = pd.read_csv(data_path)
    initial_count = len(df)
    print(f"Initial raw record count: {initial_count}")

    # Replicate TotalCharges cleanup logic from preprocess.py
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).copy()
    cleaned_count = len(df)
    print(f"Cleaned record count after dropping blank TotalCharges: {cleaned_count} (dropped {initial_count - cleaned_count} rows)")

    # Connect to SQLite database and write data
    conn = sqlite3.connect(db_path)
    try:
        # Write customers table (replace if exists)
        df.to_sql("customers", conn, if_exists="replace", index=False)
        print(f"Successfully created SQLite database at: {db_path}")

        # Verify insertion and display schema
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        print(f"Verified row count in 'customers' table: {count}")

        cursor.execute("PRAGMA table_info(customers)")
        columns = cursor.fetchall()
        print("\nTable Schema ('customers'):")
        print("-" * 50)
        for col in columns:
            cid, name, col_type, notnull, dflt_value, pk = col
            print(f"  {name:<22} | {col_type}")
        print("-" * 50)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
