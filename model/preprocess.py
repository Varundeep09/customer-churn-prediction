from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def main() -> None:
    # Build paths relative to this script so it works no matter where it is run from.
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
    model_dir = project_root / "model"

    # Load the raw dataset into a pandas DataFrame.
    df = pd.read_csv(data_path)

    # The TotalCharges column can contain blank strings.
    # First convert blank-looking values into NaN by coercing invalid entries during numeric conversion.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    # For this dataset, rows with missing TotalCharges are a very small group.
    # Dropping them keeps the preprocessing simple and matches the EDA cleanup step.
    df = df.dropna(subset=["TotalCharges"]).copy()

    # customerID is only an identifier, so it does not help the model learn patterns.
    df = df.drop(columns=["customerID"])

    # Convert the target column into binary values:
    # Yes -> 1 means the customer churned, No -> 0 means they stayed.
    df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})

    # Separate features from the target so we can preprocess the inputs only.
    X = df.drop(columns=["Churn"])
    y = df["Churn"]

    # Keep these numeric features as continuous values.
    numeric_columns = ["tenure", "MonthlyCharges", "TotalCharges"]

    # Everything stored as object/category is treated as categorical and expanded with one-hot encoding.
    categorical_columns = X.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    X_encoded = pd.get_dummies(X, columns=categorical_columns, drop_first=True)

    # Split before scaling so the scaler learns only from the training data.
    # Stratify keeps the churn ratio similar in both train and test sets.
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded,
        y,
        test_size=0.2,
        stratify=y,
        random_state=42,
    )

    # StandardScaler centers and scales numeric features to comparable ranges.
    # We fit on training data only, then apply the same transformation to test data.
    numeric_dtype_map = {column: float for column in numeric_columns}
    X_train = X_train.astype(numeric_dtype_map)
    X_test = X_test.astype(numeric_dtype_map)

    scaler = StandardScaler()
    X_train.loc[:, numeric_columns] = scaler.fit_transform(X_train[numeric_columns])
    X_test.loc[:, numeric_columns] = scaler.transform(X_test[numeric_columns])

    # Save the processed datasets, the fitted scaler, and the feature names for later reuse.
    joblib.dump(X_train, model_dir / "X_train.pkl")
    joblib.dump(X_test, model_dir / "X_test.pkl")
    joblib.dump(y_train, model_dir / "y_train.pkl")
    joblib.dump(y_test, model_dir / "y_test.pkl")
    joblib.dump(scaler, model_dir / "scaler.pkl")
    joblib.dump(X_encoded.columns.tolist(), model_dir / "feature_columns.pkl")

    # Confirm the final dataset sizes and that no missing values remain after preprocessing.
    print(f"X_train shape: {X_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"Missing values in X_train: {int(X_train.isna().sum().sum())}")
    print(f"Missing values in X_test: {int(X_test.isna().sum().sum())}")
    print(f"Missing values in y_train: {int(y_train.isna().sum())}")
    print(f"Missing values in y_test: {int(y_test.isna().sum())}")
    print("Preprocessing complete. Artifacts saved in the model directory.")


if __name__ == "__main__":
    main()
