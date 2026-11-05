
from pathlib import Path
import pandas as pd

# Project paths
INPUT_FILE = Path(
    "data/raw/accepted_2007_to_2018q4.csv/"
    "accepted_2007_to_2018Q4.csv"
)
OUTPUT_FILE = Path("data/processed/credit_risk_clean.csv")

# Features known when the loan was issued.
FEATURES = [
    "loan_amnt",
    "term",
    "int_rate",
    "installment",
    "grade",
    "emp_length",
    "home_ownership",
    "annual_inc",
    "verification_status",
    "purpose",
    "dti",
    "delinq_2yrs",
    "fico_range_low",
    "fico_range_high",
    "inq_last_6mths",
    "open_acc",
    "pub_rec",
    "revol_bal",
    "revol_util",
    "total_acc",
]

USE_COLUMNS = FEATURES + ["loan_status"]

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Remove an older output so reruns do not duplicate rows.
if OUTPUT_FILE.exists():
    OUTPUT_FILE.unlink()

total_rows = 0
saved_rows = 0
first_chunk = True

for chunk in pd.read_csv(
    INPUT_FILE,
    usecols=USE_COLUMNS,
    chunksize=100_000,
    low_memory=False,
):
    total_rows += len(chunk)

    # Keep only clearly resolved loan outcomes.
    chunk = chunk[
        chunk["loan_status"].isin(
            ["Fully Paid", "Charged Off", "Default"]
        )
    ].copy()

    # 0 = Fully Paid; 1 = Charged Off or Default.
    chunk["bad_loan"] = (
        chunk["loan_status"].isin(["Charged Off", "Default"])
    ).astype("int8")

    # Remove the original outcome text from model features.
    chunk.drop(columns=["loan_status"], inplace=True)

    chunk.to_csv(
        OUTPUT_FILE,
        index=False,
        mode="w" if first_chunk else "a",
        header=first_chunk,
    )

    saved_rows += len(chunk)
    first_chunk = False

print(f"Rows scanned: {total_rows:,}")
print(f"Eligible loans saved: {saved_rows:,}")
print(f"Output file: {OUTPUT_FILE}")
print("\nSaved dataset preview:")
print(pd.read_csv(OUTPUT_FILE, nrows=5).to_string(index=False))
