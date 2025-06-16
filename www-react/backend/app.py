# app.py

import os
import datetime
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from database_utils import DBManager  # Your existing DB logic

import statsmodels.api as sm
import numpy as np

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS so React can call this API from a different domain/port

db_manager = DBManager()
ALPHA = 0.1

################################################################################
# 1) In-memory or DB storage for V (stimuli "value")
################################################################################
# For a real production app, you'd store these in a database table
# so that you don't lose them if the server restarts. Here is an in-memory dict:
V_values = {}
# Example: V_values[sequence_id] = { resource_id_1: 0.0, resource_id_2: 0.0, ... }


################################################################################
# 2) Utility: get or create participant
################################################################################
def get_or_create_participant(participant_name, participant_equipment=""):
    """
    Look up participant in DB by name and equipment; if not found, create and return its ID.
    """
    db_manager.connect()
    df_participants = db_manager.read_table("participants")
    existing = df_participants[
        (df_participants["participant_name"] == participant_name)
        & (df_participants["equipments"] == participant_equipment)
    ]
    if not existing.empty:
        participant_id = int(existing.iloc[0]["id"])
    else:
        new_row = pd.DataFrame(
            [
                {
                    "participant_name": participant_name,
                    "equipments": participant_equipment,
                }
            ]
        )
        db_manager.append_table("participants", new_row)
        df_participants = db_manager.read_table("participants")
        new_entry = df_participants[
            (df_participants["participant_name"] == participant_name)
            & (df_participants["equipments"] == participant_equipment)
        ]
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
    each trial's resource_ids in order. Also ensures V_values exist.
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

    # Also build an "audio_map" so the frontend can display correct audio paths
    # (The React app can then do <audio src=... /> or something similar)
    audio_map = {}
    for _, row in df_view.iterrows():
        res_id = row["resource_id"]
        folder_path = row["folder_path"]
        filename = row["resource_filenames"]
        # audio_path = os.path.join(folder_path, filename)

        audio_path = row["resource_folder_paths"]
        audio_map[res_id] = audio_path
        logging.info(f"audio_map: {audio_map}")

    return jsonify(
        {
            "trials": trials,  # list of lists
            "audio_map": audio_map,  # { resource_id: audio_path }
        }
    )


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
    Then updates "V" for best/worst, saves trial results in DB.
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

    # Insert row into "trial_results"
    db_manager.connect()
    df_trial = pd.DataFrame(
        [
            {
                "participant_id": participant_id,
                "sequence_id": sequence_id,
                "trial_index": trial_index,
                "best_stimulus": best_res_id,
                "worst_stimulus": worst_res_id,
                "submitted_at": datetime.datetime.now(),
            }
        ]
    )
    db_manager.append_table("trial_results", df_trial)

    return jsonify({"message": "Submitted successfully"})


@app.route(
    "/api/trials/<int:sequence_id>/<int:trial_index>/submit_similar", methods=["POST"]
)
def submit_trial_similar(sequence_id, trial_index):
    """
    Receives JSON:
      {
        "participant_name": "Alice",
        "participant_equipment": "Sony WH-1000XM4",
        "ratings": {
            "stimulus_id1": rating_value1,
            "stimulus_id2": rating_value2,
            ...
        },
        "resources_in_trial": [reference_id, stimulus_id1, stimulus_id2, ...]
      }
    Then saves similarity ratings in DB.
    """
    data = request.json
    participant_name = data.get("participant_name")
    participant_equipment = data.get("participant_equipment", "")
    ratings = data.get("ratings", {})
    resources_in_trial = data.get("resources_in_trial", [])

    if not participant_name or not resources_in_trial:
        return jsonify({"error": "Missing required fields"}), 400

    participant_id = get_or_create_participant(participant_name, participant_equipment)
    reference_id = resources_in_trial[0]  # First resource is always reference

    # Insert rows into "similarity_ratings"
    db_manager.connect()
    now = datetime.datetime.now()

    for stimulus_id, rating_value in ratings.items():
        df_rating = pd.DataFrame(
            [
                {
                    "participant_id": participant_id,
                    "sequence_id": sequence_id,
                    "trial_index": trial_index,
                    "reference_stimulus": reference_id,
                    "rated_stimulus": int(stimulus_id),
                    "rating_value": rating_value,
                    "submitted_at": now,
                }
            ]
        )
        db_manager.append_table("similarity_ratings", df_rating)

    return jsonify({"message": "Submitted successfully"})


################################################################################
# 5) Endpoint: finalize and compute final ranking
################################################################################
@app.route("/api/trials/<int:sequence_id>/finalize", methods=["POST"])
def finalize(sequence_id):
    """
    Computes final similarity scores by averaging ratings for each stimulus
    """
    data = request.json
    participant_name = data.get("participant_name")
    if not participant_name:
        return jsonify({"error": "Missing participant_name"}), 400

    participant_id = get_or_create_participant(participant_name)

    # Load all similarity ratings for this sequence_id and participant
    db_manager.connect()
    df_ratings = db_manager.read_table("similarity_ratings")
    df_ratings = df_ratings[
        (df_ratings["sequence_id"] == sequence_id)
        & (df_ratings["participant_id"] == participant_id)
    ].copy()

    if df_ratings.empty:
        return (
            jsonify({"error": "No ratings found for this participant and sequence."}),
            404,
        )

    # Calculate average similarity score for each stimulus
    stimulus_scores = df_ratings.groupby("rated_stimulus")["rating_value"].mean()
    sorted_stimuli = stimulus_scores.sort_values(ascending=False)

    # Fetch resource filenames from sequence_view
    df_view = db_manager.read_table("sequence_view")
    df_view = df_view[df_view["sequence_id"] == sequence_id].copy()
    file_map = {
        row["resource_id"]: row["resource_filenames"] for _, row in df_view.iterrows()
    }

    # Save final scores to database
    now = datetime.datetime.now()
    final_scores = []
    for rank, (res_id, score) in enumerate(sorted_stimuli.items(), 1):
        final_scores.append(
            {
                "participant_id": participant_id,
                "sequence_id": sequence_id,
                "resource_id": int(res_id),
                "average_similarity": float(score),
                "rank_position": rank,
                "computed_at": now,
            }
        )

    df_final = pd.DataFrame(final_scores)
    db_manager.append_table("similarity_final_scores", df_final)

    # Format output JSON
    sorted_stimuli_list = [
        {
            "resource_id": int(res_id),
            "score": float(score),
            "filename": file_map.get(res_id, ""),
        }
        for res_id, score in sorted_stimuli.items()
    ]

    return jsonify(
        {
            "sorted_stimuli": sorted_stimuli_list,
            "message": "Final similarity scores computed and saved.",
        }
    )


################################################################################
# Run
################################################################################
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
