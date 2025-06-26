import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_squared_error
import shap
import numpy as np
import matplotlib.pyplot as plt

from database_utils import DBManager

from scipy.optimize import minimize
from scipy.special import logsumexp

def compute_bws_scores_mnl(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame of BWS trials, compute final scores (latent utilities)
    using a Multinomial Logit (MNL) model.
    
    Each trial in df should include:
      - "resource_ids": a list of resource identifiers presented in that trial.
      - "best_stimulus": the resource id chosen as best.
      - "worst_stimulus": the resource id chosen as worst.
      - "trial_index": the order of the trial (used for sorting).
    
    The model assumes:
      P(best = b | S)   = exp(v_b) / sum_{j in S} exp(v_j)
      P(worst = w | S)  = exp(-v_w) / sum_{j in S} exp(-v_j)
      
    The negative log-likelihood over all valid trials is minimized to estimate the latent utilities.
    
    Returns a DataFrame with columns:
      - resource_id: identifier of the resource.
      - final_score: estimated latent utility.
      - rank_position: rank (1 = highest score).
    """
    # 1) Gather all unique resource IDs and create a mapping to indices
    all_resources = set()
    for resource_list in df["resource_ids"]:
        all_resources.update(resource_list)
    all_resources = sorted(list(all_resources))
    resource_to_index = {res_id: idx for idx, res_id in enumerate(all_resources)}
    n_resources = len(all_resources)
    
    # 2) Prepare the list of valid trials (skip trials with missing best/worst)
    trials = []
    df_sorted = df.sort_values(by="trial_index").reset_index(drop=True)
    for _, row in df_sorted.iterrows():
        resources = row["resource_ids"]
        best = row["best_stimulus"]
        worst = row["worst_stimulus"]
        if pd.isna(best) or pd.isna(worst):
            continue
        if best not in resource_to_index or worst not in resource_to_index:
            continue
        trials.append((resources, best, worst))
    
    # 3) Define the negative log-likelihood function
    def neg_log_likelihood(v):
        ll = 0.0
        for resources, best, worst in trials:
            # Convert the resource ids in this trial to indices
            indices = [resource_to_index[r] for r in resources]
            v_resources = v[indices]
            # For the best choice: use logsumexp for stability
            v_best = v[resource_to_index[best]]
            log_prob_best = v_best - logsumexp(v_resources)
            # For the worst choice: use logsumexp on -v_resources for stability
            v_worst = v[resource_to_index[worst]]
            log_prob_worst = -v_worst - logsumexp(-v_resources)
            ll += (log_prob_best + log_prob_worst)
        return -ll  # negative log-likelihood for minimization

    # 4) Initial guess for v: zeros
    initial_v = np.zeros(n_resources)
    
    # 5) Optimize the negative log-likelihood
    result = minimize(neg_log_likelihood, initial_v, method='BFGS')
    estimated_v = result.x
    
    # Normalize the estimates for identification (e.g., subtract mean)
    estimated_v = estimated_v - np.mean(estimated_v)
    
    # 6) Build the final ranking DataFrame
    results_list = []
    for res_id, idx in resource_to_index.items():
        results_list.append({
            "resource_id": res_id,
            "final_score": estimated_v[idx]
        })
    # Sort items by final_score in descending order
    sorted_items = sorted(results_list, key=lambda x: x["final_score"], reverse=True)
    
    # Add rank positions
    for rank, item in enumerate(sorted_items, start=1):
        item["rank_position"] = rank
        
    return pd.DataFrame(sorted_items)

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


        # Skip this row if best or worst is NaN
        if pd.isna(best) or pd.isna(worst):
            continue

        # Also, ensure that the keys exist in V before proceeding
        if best not in V or worst not in V:
            continue
        
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

        for item in resources:
            if item == best or item == worst:
                continue
            # For intermediate items, target differences are 0.5.
            # error_from_best = 0.5 - (V[best] - V[item])  # desired: V[best] - V[item] = 0.5
            error_from_worst = 0.5 - (V[item] - V[worst])  # desired: V[item] - V[worst] = 0.5
            error = (error_from_worst)
            V[item] += alpha * error

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
    (
    (df_results["participant_id"] == 6) |
    (df_results["participant_id"] == 8) |
    (df_results["participant_id"] == 9) |
    (df_results["participant_id"] == 10)
    ) &
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
final_scores = compute_bws_scores(df_merged, alpha=0.5)
# final_scores = compute_bws_scores_mnl(df_merged)


# Read extracted features from disk
temp_csv = "temp_features.csv"
df_features = pd.read_csv(temp_csv)
print("=== Final Extracted Features ====")
# print(df_features["resource_filenames"])

# Merge the extracted features with the final scores
df_merged_features = final_scores.merge(df_features, on="resource_id", how="left")
print("=== Final Scores with Extracted Audio Features ====")
df_resource = db_manager.read_table("resources", engine)
# df_resource.rename(columns={"trial": "trial_index", "resource_id": "resource_ids"},inplace=True)
df_resource["resource_id"] = df_resource["id"]
print(df_resource.columns)
df_merged_features = df_merged_features.merge(
    df_resource[['resource_id', 'filenames']],
    on='resource_id',
    how='left'
)

# List of known amp names
amp_names = [
    "Marshall 1959Plexi",
    "Fender deluxe reverb",
    "VOXac30 custom",
    "Plugin_GTR Amp",
    "Roland Jazz Chorus",
    "Marshall JCM800",
    "Marshall 1959Plexi",
    "Orange Rocker30 Head"
]

def extract_amp_hardcoded(text):
    for amp in amp_names:
        if amp in text:
            return amp
    print(f"Unknown amp in text: {text}")
    return None  # or 'Unknown'

df_merged_features['amp'] = df_merged_features['filenames'].apply(extract_amp_hardcoded)



print(df_merged_features[['resource_id', 'amp','final_score', 'rank_position']])

# Plotting
plt.figure(figsize=(12, 6))
scatter = plt.scatter(df_merged_features['rank_position'], df_merged_features['final_score'], c=pd.factorize(df_merged_features['amp'])[0], cmap='tab10', label=df_merged_features['amp'])
plt.xlabel('Rank Position')
plt.ylabel('Final Score')
plt.title('Final Score vs. Rank by Amp')
plt.grid(True)

# Creating a legend with amp names
handles, _ = scatter.legend_elements(prop="colors")
unique_amps = pd.unique(df_merged_features['amp'])
plt.legend(handles, unique_amps, title="Amp", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 6))
df_merged_features.boxplot(column='final_score', by='amp', grid=False)
plt.title('Distribution of Final Score by Amp')
plt.suptitle('')
plt.xlabel('Amp')
plt.ylabel('Final Score')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
# -------------------- Modeling --------------------
# Define feature columns and target variable
feature_columns = ["spectral_centroid_med", "spectral_centroid_iqr", 
                   "spectral_bandwidth_iqr", "f0", "hnr_med"]
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import shap

X = df_merged_features[feature_columns]
y = df_merged_features["final_score"]/df_merged_features["final_score"].max()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# --- 5-Fold Cross Validation ---
kfold = KFold(n_splits=5, shuffle=True, random_state=42)
fold_metrics = []
fold = 1

for train_index, val_index in kfold.split(X_train):
    X_train_cv, X_val_cv = X_train.iloc[train_index], X_train.iloc[val_index]
    y_train_cv, y_val_cv = y_train.iloc[train_index], y_train.iloc[val_index]

    model_cv = xgb.XGBRegressor(objective='reg:squarederror', random_state=42,learning_rate=0.1)
    model_cv.fit(X_train_cv, y_train_cv)

    y_pred_val = model_cv.predict(X_val_cv)

    mse = mean_squared_error(y_val_cv, y_pred_val)
    mae = mean_absolute_error(y_val_cv, y_pred_val)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_val_cv, y_pred_val)

    fold_metrics.append({
        'fold': fold,
        'MSE': mse,
        'RMSE': rmse,
        'MAE': mae,
        'R2': r2
    })

    print(f"Fold {fold}: MSE: {mse:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")
    fold += 1


plt.plot(y_test.sort_values(ascending=False).values)


# 3. Train final model on all training data
final_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42, learning_rate=0.1,n_estimators=10000)
final_model.fit(X_train, y_train)

print("min: ", min(y_train)," max: ", max(y_train))

# 4. Evaluate on the hold-out test set
y_pred_test = final_model.predict(X_test)

# plt.plot(y_pred_test.sort_values(ascending=False).values)
# plt.title("Final Scores")
# plt.show()
mse_test = mean_squared_error(y_test, y_pred_test)
mae_test = mean_absolute_error(y_test, y_pred_test)
rmse_test = np.sqrt(mse_test)

print("\nFinal Model Metrics on Test Set:")
print(f"MSE: {mse_test:.4f}, RMSE: {rmse_test:.4f}, MAE: {mae_test:.4f}")

# # SHAP Explanation (on test set or full train set)
explainer = shap.Explainer(final_model)
shap_values = explainer(X)

shap.summary_plot(shap_values, X)

