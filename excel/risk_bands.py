from pathlib import Path

import joblib
import pandas as pd

INPUT_FILE = Path("data/processed/credit_risk_clean.csv")
MODEL_FILE = Path("output/credit_risk_logistic_model.joblib")
OUTPUT_FILE = Path("output/credit_risk_scored_detail.csv")

# Load the existing trained model.
model = joblib.load(MODEL_FILE)

# Read the first 50,000 loans.
df = pd.read_csv(INPUT_FILE, nrows=50000)

# Keep the actual outcome separately.
actual_outcome = df["bad_loan"].copy()
X = df.drop(columns=["bad_loan"])

# Predict the probability of a bad loan.
df["bad_loan_probability"] = model.predict_proba(X)[:, 1]

# Assign risk bands.
df["risk_band"] = pd.cut(
    df["bad_loan_probability"],
    bins=[-0.001, 0.30, 0.60, 1.0],
    labels=["Low Risk", "Medium Risk", "High Risk"],
)

df["actual_bad_loan"] = actual_outcome

# Save detailed loan-level results to a NEW file.
df.to_csv(OUTPUT_FILE, index=False)

print("Scored data shape:", df.shape)

print("\nRisk band counts:")
print(df["risk_band"].value_counts().sort_index())

print("\nAverage predicted bad-loan probability by risk band:")
print(
    df.groupby("risk_band", observed=False)["bad_loan_probability"]
    .mean()
    .round(3)
)

print(f"\nDetailed scored data saved to: {OUTPUT_FILE}")