import pandas as pd
import random
import time
from datetime import datetime
from database_utils import DBManager

def generate_trials(stimuli, choice_set_size, n_trials):
    """
    Generate a list of trials, where each trial is a list
    of `choice_set_size` distinct stimulus IDs.
    """
    return [
        random.sample(stimuli, choice_set_size)
        for _ in range(n_trials)
    ]

def main():
    folder_path = r"D:\Desktop\Piano"
    choice_set_size = 3
    n_trials = 5
    # If you want each new sequence to have a unique ID, set it here
    # e.g., read from a config or generate programmatically
    sequence_id = 5
    sequence_name = "Test Sequence Note"
    
    db_manager = DBManager()
    try:
        # 1) Connect to database
        engine = db_manager.connect()
        
        # 2) Get the list of resource IDs from the "resources" table for a given folder_path
        df_resources = db_manager.read_table("resources")
        df_filtered = df_resources.loc[df_resources["folder_paths"] == folder_path, "id"]
        stimuli_ids = df_filtered.tolist()

        # 3) Generate the trials
        data = generate_trials(stimuli_ids, choice_set_size, n_trials)

        # 4) Build the DataFrame rows for our "sequences" table
        df_data = [
            [sequence_id, stim_id, trial_idx, order_idx]
            for trial_idx, trial_pair in enumerate(data)
            for order_idx, stim_id in enumerate(trial_pair)
        ]
        df_final = pd.DataFrame(df_data, columns=["sequence_id", "stimuli_id", "trial", "index_order"])
        
        print("Trial DataFrame (for 'sequences' table):")
        print(df_final)

        # 5) Insert a row into "sequence_info"
        #    We'll use a single-row DataFrame to match the DB structure
        df_sequence_info = pd.DataFrame([{
            "sequence_id": sequence_id,
            "sequence_name": sequence_name,
            "time_created": datetime.now(),  # current timestamp
            "folder_path": folder_path,
            "choice_set_size": choice_set_size,
            "n_trials": n_trials
        }])
        
        print("\nSequence Info DataFrame (for 'sequence_info' table):")
        print(df_sequence_info)

        # 6) Append to the "sequence_info" table
        db_manager.append_table("sequence_info", df_sequence_info)

        # 7) Append the trial data to the "sequences" table
        db_manager.append_table("sequences", df_final)

        print("\nData inserted successfully into 'sequence_info' and 'sequences'.")

    finally:
        # Ensure that the connection is closed even if an error occurs
        db_manager.close()

if __name__ == "__main__":
    main()
