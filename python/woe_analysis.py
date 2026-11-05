
from pathlib import Path

import numpy as np
import pandas as pd

INPUT_FILE = Path("data/processed/credit_risk_clean.csv")
OUTPUT_FILE = Path("output/woe_analysis.csv")

# Load the cleaned loan data.
df = pd.read_csv(INPUT_FILE)

# Use a manageable sample for the first analysis.
if len(df) > 200_000:
    df = df.sample(n=200_000, random_state=42)

# Convert interest rate to numeric if needed.
df["int_rate"] = pd.to_numeric(df["int_rate"], errors="coerce")

# Group numeric variables into bins.
df["interest_rate_band"] = pd.cut(
    df["int_rate"],
    bins=[-np.inf, 10, 15, 20, np.inf],
    labels=["Up to 10%", "10-15%", "15-20%", "Above 20%"],
)

df["annual_income_band"] = pd.cut(
    df["annual_inc"],
    bins=[-np.inf, 30000, 60000, 100000, np.inf],
    labels=["Up to 30k", "30k-60k", "60k-100k", "Above 100k"],
)

# Calculate WoE and Information Value for each category.
def calculate_woe(data, feature, target="bad_loan"):
    grouped = (
        data.groupby(feature, observed=False)[target]
        .agg(["count", "sum"])
        .reset_index()
    )

    grouped = grouped.rename(columns={"sum": "bad_count"})
    grouped["good_count"] = grouped["count"] - grouped["bad_count"]

    # Smoothing avoids division by zero for empty categories.
    total_good = grouped["good_count"].sum()
    total_bad = grouped["bad_count"].sum()
    categories = len(grouped)

    grouped["good_distribution"] = (
        (grouped["good_count"] + 0.5)
        / (total_good + 0.5 * categories)
    )
    grouped["bad_distribution"] = (
        (grouped["bad_count"] + 0.5)
        / (total_bad + 0.5 * categories)
    )

    grouped["woe"] = np.log(
        grouped["good_distribution"] / grouped["bad_distribution"]
    )

    grouped["iv_component"] = (
        grouped["good_distribution"] - grouped["bad_distribution"]
    ) * grouped["woe"]

    grouped.insert(0, "feature", feature)
    return grouped


features = [
    "grade",
    "home_ownership",
    "verification_status",
    "purpose",
    "interest_rate_band",
    "annual_income_band",
]

results = []

for feature in features:
    table = calculate_woe(df, feature)
    table["information_value"] = table["iv_component"].sum()
    results.append(table)

final_results = pd.concat(results, ignore_index=True)
final_results.to_csv(OUTPUT_FILE, index=False)

print("WoE analysis completed.")
print("\nInformation Value by feature:")
print(
    final_results.groupby("feature")["iv_component"]
    .sum()
    .sort_values(ascending=False)
    .round(4)
)

print(f"\nDetailed WoE results saved to: {OUTPUT_FILE}")
