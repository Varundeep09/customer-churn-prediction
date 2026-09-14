import json
from datetime import date
from pathlib import Path

import joblib
import matplotlib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def evaluate_model(model_name: str, model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    # Make predictions on the test set so we can measure how well the model generalizes.
    y_pred = model.predict(X_test)

    # Accuracy = overall percentage of correct predictions.
    # It is useful, but it can be misleading for imbalanced problems like churn.
    accuracy = accuracy_score(y_test, y_pred)

    # Precision = of the customers predicted to churn, how many actually churned.
    # This matters when false alarms are costly.
    precision = precision_score(y_test, y_pred)

    # Recall = of the customers who truly churned, how many the model found.
    # This matters when missing churners is costly.
    recall = recall_score(y_test, y_pred)

    # F1-score balances precision and recall in one number.
    # For churn problems, it is often more informative than accuracy alone.
    f1 = f1_score(y_test, y_pred)

    cm = confusion_matrix(y_test, y_pred)

    print(f"\n{'=' * 60}")
    print(f"{model_name} Results")
    print(f"{'=' * 60}")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-score:  {f1:.4f}")
    print("Confusion matrix:")
    print(cm)

    return {
        "model_name": model_name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": cm.tolist(),
    }


def main() -> None:
    # Build paths relative to this script so the training step is easy to rerun.
    model_dir = Path(__file__).resolve().parent

    # Load the train/test artifacts prepared by the preprocessing script.
    X_train = joblib.load(model_dir / "X_train.pkl")
    X_test = joblib.load(model_dir / "X_test.pkl")
    y_train = joblib.load(model_dir / "y_train.pkl")
    y_test = joblib.load(model_dir / "y_test.pkl")

    # Train a simple, interpretable baseline model.
    logistic_model = LogisticRegression(max_iter=1000)
    logistic_model.fit(X_train, y_train)

    # Train a tree-based ensemble model that can capture more complex patterns.
    random_forest_model = RandomForestClassifier(n_estimators=200, random_state=42)
    random_forest_model.fit(X_train, y_train)

    logistic_results = evaluate_model("Logistic Regression", logistic_model, X_test, y_test)
    random_forest_results = evaluate_model("Random Forest Classifier", random_forest_model, X_test, y_test)

    # Put both models in one table so they are easy to compare side by side.
    comparison_df = pd.DataFrame(
        [
            {
                "Model": logistic_results["model_name"],
                "Accuracy": logistic_results["accuracy"],
                "Precision": logistic_results["precision"],
                "Recall": logistic_results["recall"],
                "F1-score": logistic_results["f1_score"],
            },
            {
                "Model": random_forest_results["model_name"],
                "Accuracy": random_forest_results["accuracy"],
                "Precision": random_forest_results["precision"],
                "Recall": random_forest_results["recall"],
                "F1-score": random_forest_results["f1_score"],
            },
        ]
    )

    print(f"\n{'=' * 60}")
    print("Model Comparison")
    print(f"{'=' * 60}")
    print(comparison_df.to_string(index=False, float_format=lambda value: f"{value:.4f}"))

    # Random Forest feature importances show which features contributed most to the splits.
    feature_importance_df = (
        pd.DataFrame(
            {
                "feature": X_train.columns,
                "importance": random_forest_model.feature_importances_,
            }
        )
        .sort_values("importance", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    print(f"\n{'=' * 60}")
    print("Top 10 Random Forest Feature Importances")
    print(f"{'=' * 60}")
    print(feature_importance_df.to_string(index=False, float_format=lambda value: f"{value:.4f}"))

    # Save a simple chart so the most important features are easy to review visually later.
    plt.figure(figsize=(10, 6))
    plt.barh(feature_importance_df["feature"], feature_importance_df["importance"], color="steelblue")
    plt.gca().invert_yaxis()
    plt.title("Top 10 Random Forest Feature Importances")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(model_dir / "feature_importance.png", dpi=150)
    plt.close()

    # Pick the final model based on F1-score because it balances precision and recall.
    if random_forest_results["f1_score"] > logistic_results["f1_score"]:
        final_model_name = "Random Forest Classifier"
        final_model = random_forest_model
        final_results = random_forest_results
    else:
        final_model_name = "Logistic Regression"
        final_model = logistic_model
        final_results = logistic_results

    joblib.dump(final_model, model_dir / "churn_model.pkl")

    model_info = {
        "chosen_model": final_model_name,
        "accuracy": round(final_results["accuracy"], 4),
        "precision": round(final_results["precision"], 4),
        "recall": round(final_results["recall"], 4),
        "f1_score": round(final_results["f1_score"], 4),
        "date_trained": date.today().isoformat(),
    }

    with open(model_dir / "model_info.json", "w", encoding="utf-8") as json_file:
        json.dump(model_info, json_file, indent=2)

    print(f"\nFinal model selected: {final_model_name}")
    print(f"Model info saved to: {model_dir / 'model_info.json'}")
    print(f"Feature importance chart saved to: {model_dir / 'feature_importance.png'}")


if __name__ == "__main__":
    main()
