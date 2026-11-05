
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
import joblib

INPUT_FILE = Path("data/processed/credit_risk_clean.csv")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Use a reproducible sample for the first model.
df = pd.read_csv(INPUT_FILE)
if len(df) > 200_000:
    df = df.sample(n=200_000, random_state=42)

target = "bad_loan"
X = df.drop(columns=[target])
y = df[target]

numeric_features = X.select_dtypes(include="number").columns.tolist()
categorical_features = X.select_dtypes(
    include=["object", "str", "category"]
).columns.tolist()

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )),
])

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    stratify=y,
    random_state=42,
)

print("Training model...")
model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]

print("\nClassification report:")
print(classification_report(
    y_test, predictions,
    target_names=["Good loan", "Bad loan"],
    zero_division=0,
))

print("Confusion matrix:")
print(confusion_matrix(y_test, predictions))

print(f"\nROC-AUC: {roc_auc_score(y_test, probabilities):.4f}")

model_path = OUTPUT_DIR / "credit_risk_logistic_model.joblib"
joblib.dump(model, model_path)
print(f"\nSaved model: {model_path}")
