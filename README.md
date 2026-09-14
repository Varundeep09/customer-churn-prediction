# Customer Churn Prediction & Retention Intelligence System

## Project Overview

This project is an end-to-end Machine Learning and Decision Intelligence platform designed to identify telecom customers at risk of churn and automate data-driven retention interventions. Using the IBM Telco Customer Churn dataset (7,043 records), the system combines rigorous statistical root-cause analysis, a dedicated SQL analytics data warehouse, and a calibrated classification model with a real-time FastAPI inference engine and interactive web dashboard.

---

## Key Results at a Glance

* **Production Model Performance:** Logistic Regression achieved **80.45% Accuracy** and **60.88% F1-Score**, outperforming Random Forest across Accuracy, Precision, Recall (+6.95%), and F1-Score (+5.26%).
* **Primary Statistical Churn Driver:** Month-to-month contracts have the strongest statistical association with attrition ($\chi^2 = 1179.55, p < 0.0001, \text{Cramér's } V = 0.410$).
* **Primary Protective Factor:** Customer tenure exhibits the strongest protective effect against churn ($r = -0.3540, p < 0.0001$).
* **Critical SQL Revenue Finding:** First-year customers churn at **47.68%**; high-value accounts ($>\$70/\text{month}$) represent **$323,148/month** in recurring revenue at stake.
* **Actionable Retention Playbook:** 6 data-backed customer segments mapped to specific retention workflows and wired directly into the live prediction UI.

---

## Tech Stack

- **Machine Learning & Statistics:** Python, Pandas, NumPy, Scikit-learn, SciPy, Matplotlib, Seaborn, Joblib
- **Database & SQL Analytics:** SQLite 3, Structured `.sql` Query Suite
- **API & Backend:** FastAPI, Uvicorn, Pydantic
- **Frontend & UI:** HTML5, CSS3 (Custom Design System), JavaScript (ES2020), Chart.js

---

## Project Structure

```text
customer-churn-prediction/
├── api/
│   └── main.py                          # FastAPI real-time prediction service
├── dashboard/
│   ├── index.html                       # Web dashboard UI with playbook integration
│   ├── style.css                        # Modern CSS design system
│   └── script.js                        # Form handling, API integration & Chart.js charts
├── data/
│   └── WA_Fn-UseC_-Telco-Customer-Churn.csv  # IBM Telco raw dataset (7,043 rows)
├── model/
│   ├── churn_model.pkl                  # Trained Logistic Regression model artifact
│   ├── churn_playbook.json              # Structured business retention action rules
│   ├── feature_columns.pkl              # Saved training feature schema
│   ├── feature_importance.png           # Feature importance visualization
│   ├── model_info.json                  # Model metadata and evaluation metrics
│   ├── preprocess.py                    # Cleaning, encoding, scaling & split pipeline
│   ├── root_cause_analysis.py           # Statistical hypothesis testing (Chi-Square & Point-Biserial)
│   ├── root_cause_findings.json         # Statistically ranked churn drivers
│   ├── scaler.pkl                       # Fitted StandardScaler artifact
│   ├── train.py                         # Model training and benchmark script
│   ├── X_test.pkl, X_train.pkl          # Feature train/test splits
│   └── y_test.pkl, y_train.pkl          # Target train/test splits
├── notebooks/
│   └── 01_eda.ipynb                     # Exploratory Data Analysis & visualizations
├── sql/
│   ├── build_database.py                # Database creation script (ingests to churn.db)
│   ├── churn.db                         # SQLite database with `customers` table
│   ├── queries/                         # Dedicated analytical SQL queries
│   │   ├── churn_by_tenure_cohort.sql
│   │   ├── churn_by_contract_type.sql
│   │   ├── churn_by_payment_method.sql
│   │   ├── churn_by_customer_value.sql
│   │   ├── churn_by_service_combo.sql
│   │   └── high_value_at_risk.sql
│   ├── query_results/                   # Exported query results (CSV)
│   └── run_all_queries.py               # SQL query execution & export runner
├── .gitignore
├── requirements.txt                     # Python dependencies
└── README.md
```

---

## Dataset

- **Dataset:** IBM Telco Customer Churn
- **Source:** Kaggle / IBM Sample Data
- **File:** `data/WA_Fn-UseC_-Telco-Customer-Churn.csv`
- **Size:** 7,043 customer records, 21 attributes (demographic, subscribed services, contract type, billing channels, and churn label).

---

## 1. Exploratory Data Analysis (EDA)

Exploratory analysis was conducted in `notebooks/01_eda.ipynb`:
- **Class Distribution:** Moderately imbalanced: `73.46%` retained vs `26.54%` churned.
- **Contract Risk:** Month-to-month contracts exhibit high churn (~42.7%) compared to multi-year contracts (~2.8%).
- **Tenure Risk:** Customers in their first year (0–12 months) account for the majority of churn events (~47.4%).
- **Data Quality:** Identified 11 blank string entries in `TotalCharges` requiring numeric coercion and cleaning.

---

## 2. Preprocessing Pipeline (`model/preprocess.py`)

1. Coerces `TotalCharges` to numeric and drops the 11 `NaN` records (retaining 7,032 clean rows).
2. Drops non-predictive `customerID`.
3. Encodes binary target: `Churn` (`Yes=1`, `No=0`).
4. One-hot encodes categoricals using `pd.get_dummies(..., drop_first=True)`.
5. Performs stratified 80/20 train/test split (`random_state=42`) to preserve class proportions.
6. Scales continuous features (`tenure`, `MonthlyCharges`, `TotalCharges`) using `StandardScaler` fitted on the training split only.
7. Persists artifacts (`scaler.pkl`, `feature_columns.pkl`, datasets) via `joblib`.

---

## 3. Modeling & Benchmark Results (`model/train.py`)

Two classification models were trained and benchmarked:
- **Logistic Regression** (`max_iter=1000`)
- **Random Forest Classifier** (`n_estimators=200`, `random_state=42`)

### Benchmark Comparison (Test Set: $N=1,407$)

| Model | Accuracy | Precision | Recall | F1-Score | Status |
|---|---:|---:|---:|---:|---|
| **Logistic Regression** | **0.8045** | **0.6505** | **0.5722** | **0.6088** | **Selected / Deployed** |
| Random Forest Classifier | 0.7868 | 0.6225 | 0.5027 | 0.5562 | Baseline Comparison |

* **Selection Rationale:** Logistic Regression won decisively across all 4 evaluation metrics. It captured 26 more true churners than Random Forest (yielding a +6.95% higher Recall) with superior precision and calibration.

---

## 4. Root Cause Analysis (`model/root_cause_analysis.py`)

To identify *why* customers churn beyond tree-based importance heuristics, formal statistical hypothesis testing was conducted:
- **Categorical Features:** Pearson's $\chi^2$ Test of Independence with Cramér's $V$ effect size.
- **Continuous Features:** Point-Biserial Correlation ($r$) with exact two-tailed $p$-values.

### Top Statistically Significant Churn Drivers

| Rank | Feature | Type | Test | Statistic | $p$-value | Effect Size | Finding |
|---|---|---|---|---|---|---|---|
| **1** | `Contract` | Categorical | $\chi^2$ Test | $\chi^2 = 1179.55$ | $< 0.0001$ | Cramér's $V = 0.410$ | Month-to-month contracts have the highest statistical dependency with churn. |
| **2** | `tenure` | Numeric | Point-Biserial | $r = -0.3540$ | $< 0.0001$ | $\|r\| = 0.354$ | Strong protective factor: each month of tenure significantly lowers churn risk. |
| **3** | `OnlineSecurity` | Categorical | $\chi^2$ Test | $\chi^2 = 846.68$ | $< 0.0001$ | Cramér's $V = 0.347$ | Absence of online security sharply increases customer attrition. |
| **4** | `TechSupport` | Categorical | $\chi^2$ Test | $\chi^2 = 824.93$ | $< 0.0001$ | Cramér's $V = 0.343$ | Lack of tech support leads to unresolved service friction and departures. |
| **5** | `PaymentMethod` | Categorical | $\chi^2$ Test | $\chi^2 = 645.43$ | $< 0.0001$ | Cramér's $V = 0.303$ | Electronic check users churn at 45.3% vs ~15% for automatic payments. |
| **-** | `PhoneService` | Categorical | $\chi^2$ Test | $\chi^2 = 0.87$ | $0.3499$ | $V = 0.011$ | *Not statistically significant ($p > 0.05$).* |
| **-** | `gender` | Categorical | $\chi^2$ Test | $\chi^2 = 0.48$ | $0.4905$ | $V = 0.008$ | *Not statistically significant ($p > 0.05$).* |

---

## 5. SQL Analytics Layer (`sql/`)

A dedicated SQLite data warehouse (`sql/churn.db`) was constructed to run production SQL queries answering key business questions:

1. **`churn_by_tenure_cohort.sql`**: Cohort analysis showing first-year churn (47.68%) dropping to 6.61% for 5+ year customers.
2. **`churn_by_contract_type.sql`**: Month-to-month churn (42.71%) vs Two-year contracts (2.85%).
3. **`churn_by_payment_method.sql`**: Electronic check churn (45.29%) vs Auto Credit Card (15.25%).
4. **`churn_by_customer_value.sql`**: High-value (>$70/mo) accounts represent $323,148/month in revenue at stake with a 35.38% churn rate.
5. **`churn_by_service_combo.sql`**: Fiber optic users without Tech Support or Security churn at 55.01% (vs 17.05% baseline).
6. **`high_value_at_risk.sql`**: Actionable target list of **814 accounts** ($>70/mo, month-to-month, $<12m tenure) for retention campaigns.

Run all SQL queries via:
```powershell
python sql/build_database.py
python sql/run_all_queries.py
```

---

## 6. Churn Retention Playbook (`model/churn_playbook.json`)

Translates statistical findings and SQL insights into an actionable decision matrix:

1. **Critical Risk — High-Value New Customer:** Month-to-month $\cap$ tenure $< 12\text{m} \cap \text{MonthlyCharges} > \$70$. Priority outreach within 48h; offer contract upgrade discount.
2. **Critical Risk — Unsupported Fiber Customer:** Fiber Optic $\cap$ No Tech Support $\cap$ No Security. Proactive 90-day free trial of Support & Security bundle.
3. **High Risk — Manual Payment, Month-to-Month:** Electronic check $\cap$ Month-to-month. Offer $5–$10 bill credit to migrate to automated payment.
4. **Moderate Risk — Early Tenure, Standard Plan:** Tenure 13–24m $\cap$ not on a 2-year contract. Annual renewal discount before entering high-churn window.
5. **Low Risk — Long-Term Contract Holder:** Two-year contract $\cap$ tenure $> 48\text{m}$. Loyalty perks & premium upsells.
6. **Low Risk — Fully Protected Customer:** Support $\cap$ Security $\cap$ Multi-year contract. Case study/testimonial candidates.

---

## 7. Prediction API (`api/main.py`)

Built with **FastAPI** to serve real-time predictions:
- Pre-loads model, scaler, and feature schema at startup.
- Handles one-row inference alignment with `pd.get_dummies(..., drop_first=False)` and reindexing.
- Fallback estimation for `TotalCharges = tenure * MonthlyCharges` if omitted.

### Endpoint: `POST /predict`
```json
// Request:
{
  "gender": "Female", "SeniorCitizen": 0, "Partner": "No", "Dependents": "No",
  "tenure": 2, "PhoneService": "Yes", "MultipleLines": "Yes",
  "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No",
  "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
  "StreamingMovies": "Yes", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check", "MonthlyCharges": 95.45, "TotalCharges": 190.90
}

// Response:
{
  "churn_prediction": "Yes",
  "churn_probability": 0.8232,
  "risk_level": "High"
}
```

---

## 8. Interactive Dashboard (`dashboard/`)

A vanilla HTML/CSS/JavaScript single-page application:
- **19-Field Input Form** with client-side validation.
- **Real-Time Prediction Panel** featuring animated count-up probability, risk badge, and Chart.js doughnut chart.
- **Integrated Playbook Layer:** Displays matched segment name, recommended retention action, and specific statistical citation.
- **EDA Visualizations:** Interactive charts for contract, tenure, and internet service distributions.

---

## 9. How to Run the Project

Follow these steps to run the complete end-to-end system locally:

### Step 1: Environment Setup
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Data Preprocessing & Model Training
```powershell
python model/preprocess.py
python model/train.py
```

### Step 3: Statistical Root Cause Analysis
```powershell
python model/root_cause_analysis.py
```

### Step 4: Build SQL Database & Run Queries
```powershell
python sql/build_database.py
python sql/run_all_queries.py
```

### Step 5: Start FastAPI Server
```powershell
uvicorn api.main:app --reload --port 8000
```
*Interactive Swagger API documentation is available at:* `http://127.0.0.1:8000/docs`

### Step 6: Launch Web Dashboard
Open `dashboard/index.html` directly in any web browser.
