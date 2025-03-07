# app.py

import os
import datetime
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from database_utils import DBManager  # Your existing DB logic

import statsmodels.api as sm
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS so React can call this API from a different domain/port

db_manager = DBManager()
ALPHA = 0.1

################################################################################
# 1) In-memory or DB storage for V (stimuli “value”)
################################################################################
# For a real production app, you'd store these in a database table
# so that you don't lose them if the server restarts. Here is an in-memory dict:
V_values = {}  
# Example: V_values[sequence_id] = { resource_id_1: 0.0, resource_id_2: 0.0, ... }


################################################################################
# 2) Utility: get or create participant
################################################################################
def get_or_create_participant(participant_name):
    """
    Look up participant in DB by name; if not found, create and return its ID.
    """
    db_manager.connect()
    df_participants = db_manager.read_table("participants")
    existing = df_participants[df_participants["participant_name"] == participant_name]
    if not existing.empty:
        participant_id = int(existing.iloc[0]["id"])
    else:
        new_row = pd.DataFrame([{"participant_name": participant_name}])
        db_manager.append_table("participants", new_row)
        df_participants = db_manager.read_table("participants")
        new_entry = df_participants[df_participants["participant_name"] == participant_name]
        if new_entry.empty:
            raise Exception("Failed to add new participant.")
        participant_id = int(new_entry.iloc[0]["id"])
    return participant_id


################################################################################
# 3) Endpoint: fetch or init trials for a given sequence_id
################################################################################
@app.route("/api/trials/<int:sequence_id>", methods=["GET"])
def get_trials(sequence_id):
    """
    Returns the list of trials for the given sequence_id, including
    each trial’s resource_ids in order. Also ensures V_values exist.
    """
    engine = db_manager.connect()
    # Read from your "sequence_view" (like in the PyQt code)
    df_view = db_manager.read_table("sequence_view")
    df_view = df_view[df_view["sequence_id"] == sequence_id].copy()

    if df_view.empty:
        return jsonify({"error": f"No rows found for sequence_id={sequence_id}"}), 404

    # Sort by trial, index_order
    df_view.sort_values(["trial", "index_order"], inplace=True)

    # Initialize V_values if needed
    unique_res_ids = df_view["resource_id"].unique()
    if sequence_id not in V_values:
        V_values[sequence_id] = {res_id: 0.0 for res_id in unique_res_ids}

    # Group into a list of trials
    # Each trial: [resource_id1, resource_id2, ...]
    trials = []
    for trial_id, gdf in df_view.groupby("trial"):
        trial_resources = gdf.sort_values("index_order")["resource_id"].tolist()
        trials.append(trial_resources)

    # Also build an “audio_map” so the frontend can display correct audio paths
    # (The React app can then do <audio src=... /> or something similar)
    audio_map = {}
    for _, row in df_view.iterrows():
        res_id = row["resource_id"]
        folder_path = row["folder_path"]
        filename = row["resource_filenames"]
        # audio_path = os.path.join(folder_path, filename)
        
        audio_path = row["resource_folder_paths"]
        audio_map[res_id] = audio_path
        
        print(audio_map)

    return jsonify({
        "trials": trials,                # list of lists
        "audio_map": audio_map,          # { resource_id: audio_path }
    })


################################################################################
# 4) Endpoint: submit best/worst for a single trial
################################################################################
@app.route("/api/trials/<int:sequence_id>/<int:trial_index>/submit", methods=["POST"])
def submit_trial(sequence_id, trial_index):
    """
    Receives JSON:
      {
        "participant_name": "Alice",
        "best_stimulus": 123,
        "worst_stimulus": 456,
        "resources_in_trial": [123, 456, 789]
      }
    Then updates “V” for best/worst, saves trial results in DB.
    """
    data = request.json
    participant_name = data.get("participant_name")
    best_res_id = data.get("best_stimulus")
    worst_res_id = data.get("worst_stimulus")
    resources_in_trial = data.get("resources_in_trial", [])

    if not participant_name:
        return jsonify({"error": "Missing fields in request"}), 400

    # if best_res_id == worst_res_id:
    #     return jsonify({"error": "best_stimulus and worst_stimulus cannot be the same"}), 400

    participant_id = get_or_create_participant(participant_name)

    # Insert row into “trial_results”
    db_manager.connect()
    df_trial = pd.DataFrame([{
        "participant_id": participant_id,
        "sequence_id": sequence_id,
        "trial_index": trial_index,
        "best_stimulus": best_res_id,
        "worst_stimulus": worst_res_id,
        "submitted_at": datetime.datetime.now()
    }])
    db_manager.append_table("trial_results", df_trial)

    return jsonify({"message": "Submitted successfully"})


################################################################################
# 5) Endpoint: finalize and compute final ranking
################################################################################
# @app.route("/api/trials/<int:sequence_id>/finalize", methods=["POST"])
# def finalize(sequence_id):
#     data = request.json
#     participant_name = data.get("participant_name")
#     if not participant_name:
#         return jsonify({"error": "Missing participant_name"}), 400

#     participant_id = get_or_create_participant(participant_name)

#     # Load all trial_results for this sequence_id
#     db_manager.connect()
#     df_results = db_manager.read_table("trial_results")
#     df_results = df_results[
#         (df_results["sequence_id"] == sequence_id)
#         & (df_results["participant_id"] == participant_id)
#     ].copy()

#     if df_results.empty:
#         return jsonify({"error": "No trial_results found for this participant and sequence."}), 404

#     # Get all unique resource IDs involved
#     unique_resources = pd.unique(df_results[["best_stimulus", "worst_stimulus"]].values.ravel())
#     resource_list = sorted(unique_resources)
#     resource_index = {r_id: i for i, r_id in enumerate(resource_list)}

#     # Construct pairwise "best > worst" training data
#     rows = []
#     for _, row in df_results.iterrows():
#         b = row["best_stimulus"]
#         w = row["worst_stimulus"]
#         x = np.zeros(len(resource_list))
#         x[resource_index[b]] = +1  # Best gets +1
#         x[resource_index[w]] = -1  # Worst gets -1
#         rows.append((x, 1))  # Response variable (b > w)

#     # Convert to NumPy for logistic regression
#     X = np.array([r[0] for r in rows])
#     y = np.array([r[1] for r in rows])

#     # Remove the last column as a reference to avoid singular matrix
#     X_reduced = X[:, :-1]  
#     model = sm.Logit(y, X_reduced)

#     try:
#         result = model.fit(disp=False)  # Fit model quietly
#     except Exception as e:
#         return jsonify({"error": f"Model fitting failed: {str(e)}"}), 500

#     # Get coefficients and append 0 for reference stimulus
#     coefs = result.params
#     full_params = list(coefs) + [0.0]

#     # Rank stimuli by estimated coefficients
#     resource_scores = []
#     for i, r_id in enumerate(resource_list):
#         resource_scores.append((r_id, full_params[i]))

#     resource_scores.sort(key=lambda x: x[1], reverse=True)

#     # Fetch resource filenames from sequence_view
#     df_view = db_manager.read_table("sequence_view")
#     df_view = df_view[df_view["sequence_id"] == sequence_id].copy()
#     file_map = {row["resource_id"]: row["resource_filenames"] for _, row in df_view.iterrows()}

#     # Format output JSON
#     sorted_stimuli = [
#         {
#             "resource_id": int(r_id),
#             "score": float(coeff),
#             "filename": file_map.get(r_id, ""),
#         }
#         for r_id, coeff in resource_scores
#     ]

#     return jsonify({
#         "sorted_stimuli": sorted_stimuli,
#         "summary": str(result.summary()),
#         "message": "Final scores saved using Bradley-Terry-Luce (BTL)."
#     })



################################################################################
# Run
################################################################################
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
