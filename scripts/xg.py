import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_squared_error
import shap
import numpy as np
import matplotlib.pyplot as plt

from database_utils import DBManager

def compute_bws_scores(df: pd.DataFrame, alpha: float = 0.1) -> pd.DataFrame:
    """
    Given a DataFrame of BWS trials, compute final scores by updating 
    the utility of each resource based on best/worst picks.
    """
    # 1) Gather all unique resource IDs
    all_resources = set()
    for resource_list in df["resource_ids"]:
        all_resources.update(resource_list)
    all_resources = sorted(list(all_resources))

    # 2) Initialize each resource's score to 0
    V = {res_id: 0.0 for res_id in all_resources}

    # 3) Sort by trial_index so updates happen in order
    df_sorted = df.sort_values(by="trial_index").reset_index(drop=True)

    # 4) For each trial, perform the best/worst updates
    for _, row in df_sorted.iterrows():
        resources = row["resource_ids"]
        best = row["best_stimulus"]
        worst = row["worst_stimulus"]

        # Update "best"
        for other_res_id in resources:
            if other_res_id != best:
                error = 1 - (V[best] - V[other_res_id])
                V[best] += alpha * error

        # Update "worst"
        for other_res_id in resources:
            if other_res_id != worst:
                error = 0 - (V[worst] - V[other_res_id])
                V[worst] += alpha * error

    # 5) Build final ranking
    sorted_items = sorted(V.items(), key=lambda x: x[1], reverse=True)

    # 6) Convert to DataFrame with ranks
    results_list = []
    for rank, (res_id, score) in enumerate(sorted_items, start=1):
        results_list.append({
            "resource_id": res_id,
            "final_score": score,
            "rank_position": rank
        })

    return pd.DataFrame(results_list)


# -------------------- Data Preparation --------------------
db_manager = DBManager()
engine = db_manager.connect()

# 1) Read the relevant rows from `trial_results`
df_results = db_manager.read_table("trial_results", engine)
df_results = df_results[
    (df_results["participant_id"] == 6) & 
    (df_results["sequence_id"] == 7)
].copy()

# 2) Read the relevant rows from `sequence_view`
df_seq = db_manager.read_table("sequence_view", engine)
df_seq = df_seq[df_seq["sequence_id"] == 7].copy()

# Group resource IDs by trial
df_grouped = df_seq.groupby("trial")["resource_id"].agg(list).reset_index()
df_grouped.rename(columns={"trial": "trial_index", "resource_id": "resource_ids"}, inplace=True)

# 3) Merge grouped resource IDs with trial_results
df_merged = pd.merge(df_results, df_grouped, how="left", on="trial_index")

# 4) Compute final scores
final_scores = compute_bws_scores(df_merged, alpha=0.1)

# Read extracted features from disk
temp_csv = "temp_features.csv"
df_features = pd.read_csv(temp_csv)
print("=== Final Extracted Features ====")
print(df_features)

# Merge the extracted features with the final scores
df_merged_features = final_scores.merge(df_features, on="resource_id", how="left")
print("=== Final Scores with Extracted Audio Features ====")
print(df_merged_features)

# -------------------- Modeling --------------------
# Define feature columns and target variable
feature_columns = ["spectral_centroid_med", "spectral_centroid_iqr", 
                   "spectral_bandwidth_iqr", "f0", "hnr_med"]
X = df_merged_features[feature_columns]
y = df_merged_features["final_score"]

# --- 5-Fold Cross Validation ---
kfold = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = []
fold = 1

for train_index, test_index in kfold.split(X):
    X_train_cv, X_test_cv = X.iloc[train_index], X.iloc[test_index]
    y_train_cv, y_test_cv = y.iloc[train_index], y.iloc[test_index]
    
    # Initialize and train the model on the current fold
    model_cv = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    model_cv.fit(X_train_cv, y_train_cv)
    
    # Make predictions and compute the fold's MSE
    y_pred_cv = model_cv.predict(X_test_cv)
    mse_cv = mean_squared_error(y_test_cv, y_pred_cv)
    cv_scores.append(mse_cv)
    print(f"Fold {fold} MSE: {mse_cv}")
    fold += 1

print("Average 5-Fold CV MSE:", np.mean(cv_scores))

# --- Train Final Model on Full Data ---
final_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
final_model.fit(X, y)
y_pred = final_model.predict(X)
mse_final = mean_squared_error(y, y_pred)
print("Final Model MSE on Full Data:", mse_final)

# -------------------- SHAP Explanation --------------------
# Create a SHAP explainer and compute SHAP values for all samples
explainer = shap.Explainer(final_model)
shap_values = explainer(X)

# Plot SHAP summary to visualize feature importance
shap.summary_plot(shap_values, X)
plt.show()
