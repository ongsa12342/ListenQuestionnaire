import pandas as pd
from database_utils import DBManager

import os
import numpy as np
import pandas as pd
import librosa
import xgboost as xgb
import gc
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def compute_hnr(y, sr, frame_length=2048, hop_length=512):
    """
    Compute the median Harmonics-to-Noise Ratio (HNR) in dB from an audio signal.
    Uses a simple approach: extract the harmonic component and then computes 
    the ratio between the RMS of the harmonic and the noise (y - harmonic).
    """
    # Extract the harmonic component
    y_harm = librosa.effects.harmonic(y)
    # Residual (noise) component
    y_noise = y - y_harm
    
    # Frame the signals
    frames_harm = librosa.util.frame(y_harm, frame_length=frame_length, hop_length=hop_length)
    frames_noise = librosa.util.frame(y_noise, frame_length=frame_length, hop_length=hop_length)
    
    # Compute RMS energy per frame for both components
    rms_harm = np.sqrt(np.mean(frames_harm**2, axis=0))
    rms_noise = np.sqrt(np.mean(frames_noise**2, axis=0))
    
    # Compute HNR per frame in decibels; avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        hnr_frames = 20 * np.log10(np.where(rms_noise == 0, 1e-10, rms_harm / rms_noise))
    return np.median(hnr_frames)

def extract_features(file_path):
    """
    Given a file path, load the audio and extract features:
      - Spectral Centroid (median and IQR)
      - Spectral Bandwidth IQR
      - Fundamental Frequency (median F0)
      - HNR (median)
    """
    # Load audio
    y, sr = librosa.load(file_path, sr=None)
    
    # Spectral Centroid
    spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    spectral_centroid_med = np.median(spec_centroid)
    spectral_centroid_iqr = np.percentile(spec_centroid, 75) - np.percentile(spec_centroid, 25)
    
    # Spectral Bandwidth
    spec_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    spectral_bandwidth_iqr = np.percentile(spec_bandwidth, 75) - np.percentile(spec_bandwidth, 25)
    
    # Fundamental frequency estimation using librosa.pyin
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, 
        fmin=librosa.note_to_hz('C2'), 
        fmax=librosa.note_to_hz('C7')
    )
    # Compute median F0 (ignoring unvoiced frames represented by np.nan)
    if np.all(np.isnan(f0)):
        f0_med = 0.0
    else:
        f0_med = np.nanmedian(f0)
    
    # HNR median computation
    hnr_med = compute_hnr(y, sr)
    
    return {
        "spectral_centroid_med": spectral_centroid_med,
        "spectral_centroid_iqr": spectral_centroid_iqr,
        "spectral_bandwidth_iqr": spectral_bandwidth_iqr,
        "f0": f0_med,
        "hnr_med": hnr_med
    }

def compute_bws_scores(df: pd.DataFrame, alpha: float = 0.1) -> pd.DataFrame:
    """
    Given a DataFrame of BWS trials, compute final scores by updating 
    the utility of each resource based on best/worst picks.

    The DataFrame `df` must contain the following columns:
      - trial_index: int
      - resource_ids: list of resource IDs involved in that trial
      - best_stimulus: resource ID chosen as the 'best' in that trial
      - worst_stimulus: resource ID chosen as the 'worst' in that trial
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

    # 4) For each trial, do the best/worst updates
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


if __name__ == "__main__":
    db_manager = DBManager()
    engine = db_manager.connect()

    #### 1) Read the relevant rows from `trial_results` ####
    df_results = db_manager.read_table("trial_results", engine)
    df_results = df_results[
        (df_results["participant_id"] == 6) & 
        (df_results["sequence_id"] == 7)
    ].copy()

    #### 2) Read the relevant rows from `sequence_view` ####
    df_seq = db_manager.read_table("sequence_view", engine)
    df_seq = df_seq[df_seq["sequence_id"] == 7].copy()

    # Group resource IDs by trial
    df_grouped = df_seq.groupby("trial")["resource_id"].agg(list).reset_index()

    # Rename columns to match what `compute_bws_scores` expects
    df_grouped.rename(columns={"trial": "trial_index", "resource_id": "resource_ids"}, inplace=True)

    #### 3) Merge grouped resource IDs with trial_results ####
    df_merged = pd.merge(df_results, df_grouped, how="left", on="trial_index")

    #### 4) Pass the merged DataFrame to compute_bws_scores ####
    final_scores = compute_bws_scores(df_merged, alpha=0.1)

    #### 5) Read the `resources` table and merge filenames / folder_paths ####
    df_resources = db_manager.read_table("resources", engine)
    df_resources["resource_id"] = df_resources["id"]

    # Merge the additional columns into final_scores 
    # (adjust column names as needed, e.g. if your actual columns are differently named)
    final_scores = final_scores.merge(
        df_resources[["resource_id", "filenames", "folder_paths"]],
        on="resource_id",
        how="left"
    )

    print("==== Final Scores with Resource Info ====")
    print(final_scores)

    db_manager.close()

     # Directory where audio files are stored
    audio_dir = r"D:\Desktop\Projects\ListenQuestionnaire\www-react\backend\static\Guitar"

    # Path for incremental saving of features
    temp_csv = "temp_features.csv"
    all_features = []  # Optionally, if you want to collect in memory for small datasets

    # If you're writing incrementally, you might want to remove any previous temp file
    if os.path.exists(temp_csv):
        os.remove(temp_csv)
    
    # Extract features for each audio file
    # Process files one-by-one
    for idx, row in final_scores.iterrows():
        filename = row["filenames"]
        file_path = os.path.join(audio_dir, filename)
        try:
            features = extract_features(file_path)
            features["resource_id"] = row["resource_id"]
            # Append features to the list
            all_features.append(features)
            print(f"Extracted features from {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
        
        # Optionally, write to CSV every 10 iterations to free up memory
        if (idx + 1) % 10 == 0:
            df_temp = pd.DataFrame(all_features)
            # Append to CSV without writing header after the first chunk
            df_temp.to_csv(temp_csv, mode='a', index=False, header=not os.path.exists(temp_csv))
            all_features = []  # Clear the list to free memory
        
        # Explicitly free memory
        gc.collect()

    # Write any remaining features if not yet saved
    if all_features:
        df_temp = pd.DataFrame(all_features)
        df_temp.to_csv(temp_csv, mode='a', index=False, header=not os.path.exists(temp_csv))

    # Finally, read all extracted features from disk
    df_features = pd.read_csv(temp_csv)
    print("=== Final Extracted Features ====")
    print(df_features)
    
    # Merge the extracted features with the final scores
    df_merged_features = final_scores.merge(df_features, on="resource_id", how="left")
    print("=== Final Scores with Extracted Audio Features ====")
    print(df_merged_features)
    
    # --- Train an XGBoost Regressor ---
    
    # Select feature columns and target variable
    feature_columns = ["spectral_centroid_med", "spectral_centroid_iqr", 
                       "spectral_bandwidth_iqr", "f0", "hnr_med"]
    X = df_merged_features[feature_columns]
    y = df_merged_features["final_score"]
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Define and train the XGBoost regressor
    model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    model.fit(X_train, y_train)
    
    # Make predictions and evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print("Test MSE:", mse)
