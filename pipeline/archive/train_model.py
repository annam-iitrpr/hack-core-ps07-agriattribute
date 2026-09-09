"""
train_model.py - XGBoost Model Training & SHAP Attribution Engine (Indian Agriculture Context)
Team 15 - HACK CORE 2026 (Problem Statement 07: Yield Attribution & ROI Predictor)
"""

import os
import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import shap


def train_yield_attribution_model(data_path: str = "data/field_trials.csv"):
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run data_generator.py first.")
        
    df = pd.read_csv(data_path)
    
    # Feature Selection (Base + 12-Parameter Soil Health Card features)
    feature_cols = [
        "soil_organic_carbon", "soil_ph", "nitrogen_kgha", "phosphorus_kgha", 
        "potassium_kgha", "clay_content_pct", "sulphur_ppm", "zinc_ppm", "boron_ppm",
        "cumulative_rainfall_mm", "growing_degree_days", "avg_temperature_c", "heat_stress_days", 
        "peak_ndvi", "bio_applied", "bio_dosage_l_ha"
    ]
    # Filter to features actually present in df
    feature_cols = [c for c in feature_cols if c in df.columns]
    
    # One-hot encode crop_type and region
    categorical_cols = ["crop_type", "region"]
    df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=False)
    
    encoded_feature_cols = feature_cols + [c for c in df_encoded.columns if c.startswith("crop_type_") or c.startswith("region_")]
    
    target_col = "yield_q_per_acre" if "yield_q_per_acre" in df_encoded.columns else "observed_yield_q_acre"
    X = df_encoded[encoded_feature_cols]
    y = df_encoded[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=0.2)
    
    print(f"Training XGBoost Regressor on {len(X_train)} Indian field trial samples with {len(encoded_feature_cols)} features...")
    
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.07,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluation
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    mae = mean_absolute_error(y_test, preds)
    
    print(f"--- Model Evaluation Performance ---")
    print(f"R² Score: {r2:.4f}")
    print(f"RMSE: {rmse:.2f} q/acre")
    print(f"MAE:  {mae:.2f} q/acre")
    
    # Compute SHAP Explainer
    print("Computing SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)
    
    # Bundle artifacts
    artifacts = {
        "model": model,
        "explainer": explainer,
        "feature_names": encoded_feature_cols,
        "base_feature_cols": feature_cols,
        "categorical_cols": categorical_cols,
        "all_columns": X.columns.tolist(),
        "metrics": {"r2": r2, "rmse": rmse, "mae": mae}
    }
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/model.pkl")
    joblib.dump(artifacts, "models/shap_explainer.pkl")

    import json
    metrics_info = {
        "dataset_type": "Synthetic / Demonstration Dataset",
        "dataset_path": data_path,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "total_samples": int(len(X)),
        "features_count": int(len(encoded_feature_cols)),
        "target": target_col,
        "r2": round(float(r2), 4),
        "rmse": round(float(rmse), 2),
        "mae": round(float(mae), 2),
        "disclaimer": "Model trained on synthetic calibrated Indian agronomic dataset; evaluation reflects holdout test split performance."
    }
    with open("models/model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_info, f, indent=2)

    print("SUCCESS: Saved models/model.pkl, models/shap_explainer.pkl, and models/model_metrics.json successfully!")


if __name__ == "__main__":
    train_yield_attribution_model()
