"""
Module 08 · Section 8.13 — MLflow (Tracking + Model Registry)

MLflow is the model lifecycle tool bundled with Databricks. Every ML
project needs to answer three questions:

  1. What did we train and when?         → TRACKING
  2. Which run produced this model?      → RUN LINEAGE
  3. Which model is in production?       → MODEL REGISTRY

Even for a DE role (not ML engineer), understanding MLflow matters
because you often own the pipeline that feeds the ML team.

This section demonstrates:
  * MLflow tracking with parameters, metrics, artifacts
  * Training 3 model variants and logging each
  * Querying past runs for comparison
  * Registering the best model to the Model Registry
  * Loading a registered model for inference on new data

Install first:  pip install mlflow scikit-learn
"""

import mlflow
import mlflow.sklearn
import mlflow.spark
from pyspark.sql import functions as F

# For scikit-learn model training (small, in-driver).
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import pandas as pd


# -----------------------------------------------------------------------
# Set up MLflow tracking
# -----------------------------------------------------------------------
# Locally: MLflow uses ./mlruns/ as the tracking store by default.
# In Databricks: it uses the workspace-level tracking server automatically.
# We'll set an experiment name explicitly.

mlflow.set_experiment("NovaBuild-Contractor-Risk-Prediction")


# -----------------------------------------------------------------------
# Prepare training data
# -----------------------------------------------------------------------
# Predict "high_risk" (EMR > 1.25) from contractor features.

contractors = spark.read.jdbc(url=jdbc_url, table="contractors", properties=jdbc_props)
incident_counts = (spark.read.jdbc(url=jdbc_url, table="safety_incidents", properties=jdbc_props)
    .groupBy("contractor_id")
    .agg(F.count("*").alias("incident_count"))
)

training_data = contractors.join(incident_counts, on="contractor_id", how="left") \
    .fillna({"incident_count": 0}) \
    .withColumn("high_risk", (F.col("emr") > 1.25).cast("int"))

# Bring to pandas — small dataset, fits in driver memory.
pdf = training_data.select(
    "incident_count", "employees_count", "high_risk"
).toPandas()

X = pdf[["incident_count", "employees_count"]]
y = pdf["high_risk"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)


# -----------------------------------------------------------------------
# Train 3 model variants and log each to MLflow
# -----------------------------------------------------------------------
variants = [
    {"n_estimators":  50, "max_depth": 3},
    {"n_estimators": 100, "max_depth": 5},
    {"n_estimators": 200, "max_depth": 8},
]

for i, params in enumerate(variants):
    with mlflow.start_run(run_name=f"rf-variant-{i+1}"):
        # Log parameters
        mlflow.log_params(params)

        # Train
        model = RandomForestClassifier(random_state=42, **params)
        model.fit(X_train, y_train)

        # Evaluate
        pred = model.predict(X_test)
        acc = accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred)

        # Log metrics
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)

        # Log the model itself as an artifact
        mlflow.sklearn.log_model(model, "model")

        print(f"[variant {i+1}] params={params} accuracy={acc:.3f} f1={f1:.3f}")


# -----------------------------------------------------------------------
# Query MLflow for the best run
# -----------------------------------------------------------------------
runs = mlflow.search_runs(
    experiment_names=["NovaBuild-Contractor-Risk-Prediction"],
    order_by=["metrics.f1_score DESC"],
)

print("\nTop 3 runs by F1:")
print(runs[["run_id", "metrics.accuracy", "metrics.f1_score",
            "params.n_estimators", "params.max_depth"]].head(3))

best_run_id = runs.iloc[0]["run_id"]
print(f"\nBest run: {best_run_id}")


# -----------------------------------------------------------------------
# Register the best model to the Model Registry
# -----------------------------------------------------------------------
# The registry is a versioned catalog. Each model has stages:
#   None → Staging → Production → Archived

model_uri = f"runs:/{best_run_id}/model"
model_name = "novabuild_contractor_risk_classifier"

# Register (creates version 1 on first call, version 2 next time, etc.)
result = mlflow.register_model(model_uri, model_name)
print(f"Registered {model_name} v{result.version}")

# Move to Production stage
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name=model_name,
    version=result.version,
    stage="Production",
    archive_existing_versions=True,   # move any previous Production version to Archived
)


# -----------------------------------------------------------------------
# Load the Production model + score new contractors
# -----------------------------------------------------------------------
# In a real batch scoring pipeline, this is what runs nightly.

production_model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")

# Fetch a batch of contractors to score (real pipeline would use a
# incremental / watermark pattern — see Module 04 §4.11).
new_data = pdf[["incident_count", "employees_count"]].sample(10, random_state=1)
new_data["predicted_high_risk"] = production_model.predict(new_data)
print("\nSample predictions:")
print(new_data)


# =====================================================================
# Concepts demonstrated
#
#   * MLflow tracking: log_params, log_metric, log_model
#   * Multi-variant experimentation logged to a single experiment
#   * mlflow.search_runs for programmatic comparison
#   * Model Registry with versioning + stage transitions
#   * Loading a registered model via models:/name/stage URI
#   * The DE-owned pattern: nightly batch scoring pipeline
# =====================================================================
