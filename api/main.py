from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional


# Load all saved artifacts once when the API starts.
# This keeps prediction requests fast because we do not reload files on every call.
project_root = Path(__file__).resolve().parents[1]
model_dir = project_root / "model"

model = joblib.load(model_dir / "churn_model.pkl")
scaler = joblib.load(model_dir / "scaler.pkl")
feature_columns = joblib.load(model_dir / "feature_columns.pkl")

numeric_columns = ["tenure", "MonthlyCharges", "TotalCharges"]


class CustomerData(BaseModel):
    gender: str = Field(..., examples=["Female"])
    SeniorCitizen: int = Field(..., examples=[0])
    Partner: str = Field(..., examples=["Yes"])
    Dependents: str = Field(..., examples=["No"])
    tenure: int = Field(..., examples=[12])
    PhoneService: str = Field(..., examples=["Yes"])
    MultipleLines: str = Field(..., examples=["No"])
    InternetService: str = Field(..., examples=["DSL"])
    OnlineSecurity: str = Field(..., examples=["Yes"])
    OnlineBackup: str = Field(..., examples=["No"])
    DeviceProtection: str = Field(..., examples=["No"])
    TechSupport: str = Field(..., examples=["No"])
    StreamingTV: str = Field(..., examples=["No"])
    StreamingMovies: str = Field(..., examples=["No"])
    Contract: str = Field(..., examples=["Month-to-month"])
    PaperlessBilling: str = Field(..., examples=["Yes"])
    PaymentMethod: str = Field(..., examples=["Electronic check"])
    MonthlyCharges: float = Field(..., examples=[70.35])
    TotalCharges: Optional[float] = Field(default=None, examples=[845.25])


app = FastAPI(
    title="Customer Churn Prediction API",
    version="1.0.0",
    description="Predicts whether a telecom customer is likely to churn based on raw customer details.",
)

# Allow frontend apps on other local ports to call this API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def prepare_input_data(customer: CustomerData) -> pd.DataFrame:
    # Build a raw input dictionary first so we can safely fill TotalCharges if it was not provided.
    raw_data = customer.model_dump()

    # If TotalCharges is missing, estimate it from tenure * MonthlyCharges.
    # This is only a fallback for new requests and keeps the API usable with a simpler input form.
    if raw_data["TotalCharges"] is None:
        raw_data["TotalCharges"] = raw_data["tenure"] * raw_data["MonthlyCharges"]

    # Convert the incoming request into a one-row DataFrame so we can reuse pandas preprocessing steps.
    input_df = pd.DataFrame([raw_data])

    # For inference, do NOT use drop_first=True on a single row.
    # On one-row inputs, pandas sees only one category value and would drop that only value,
    # which can erase important signals like Electronic check or Fiber optic entirely.
    # Instead we create all present dummy columns first, then align to the saved training schema.
    encoded_df = pd.get_dummies(input_df, drop_first=False)

    # Reindexing is the key step that keeps API inputs aligned with training-time features.
    # The saved feature list represents the exact columns the model saw during training.
    # If this single request does not create some dummy columns, we add them back with 0s.
    # If it creates any unexpected columns, reindexing drops them so the final schema stays consistent.
    aligned_df = encoded_df.reindex(columns=feature_columns, fill_value=0)

    # Scale after reindexing so the final DataFrame keeps the exact training column order.
    # Only the numeric columns are transformed; dummy columns remain as 0/1 indicators.
    aligned_df = aligned_df.astype({column: float for column in numeric_columns})
    aligned_df.loc[:, numeric_columns] = scaler.transform(aligned_df[numeric_columns])

    return aligned_df


def get_risk_level(probability: float) -> str:
    # Simple thresholds for a beginner-friendly risk label:
    # below 0.33 -> Low, 0.33 to below 0.66 -> Medium, 0.66 and above -> High.
    if probability >= 0.66:
        return "High"
    if probability >= 0.33:
        return "Medium"
    return "Low"


@app.get("/")
def root() -> dict:
    return {
        "name": "Customer Churn Prediction API",
        "version": "1.0.0",
        "description": "FastAPI service for predicting telecom customer churn.",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "message": "API is running"}


@app.post("/predict")
def predict(customer: CustomerData) -> dict:
    prepared_df = prepare_input_data(customer)

    prediction = model.predict(prepared_df)[0]
    probability = float(model.predict_proba(prepared_df)[0][1])

    return {
        "churn_prediction": "Yes" if prediction == 1 else "No",
        "churn_probability": round(probability, 4),
        "risk_level": get_risk_level(probability),
    }
