import pandas as pd
import random
import time
from datetime import datetime
from database_utils import DBManager

def create_sets_of_stimuli(stimuli_ids, repeats=3, set_size=5):
    """
    Given a list of stimulus IDs, each should appear `repeats` times overall.
    We then form sets of size `set_size` with distinct IDs until we cannot
    form a complete set. Returns a tuple (all_sets, leftover).

    all_sets is a list of lists (each sub-list is a distinct set of IDs).
    leftover is the list of IDs that are left unused because they
    could not form a complete set.
    """
    # Initialize the count for each stimulus
    file_counts = {sid: repeats for sid in stimuli_ids}
    all_sets = []

    # Keep forming sets until we don't have enough distinct items left
    while sum(1 for count in file_counts.values() if count > 0) >= set_size:
        # Collect all available stimuli
        available_files = [sid for sid, count in file_counts.items() if count > 0]
        # Randomly sample 'set_size' distinct stimuli
        group = random.sample(available_files, set_size)
        # Decrement the count of each chosen stimulus
        for sid in group:
            file_counts[sid] -= 1
        all_sets.append(group)

    # Anything left that couldn't form a full set
    leftover = [sid for sid, count in file_counts.items() for _ in range(count)]

    return all_sets, leftover

def main():
    # For demonstration purposes, adjust these as needed:
    folder_path = r"https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Guitar/"   # This matches what's in your DB
    repeats = 3                         # Each file should appear this many times total
    set_size = 5                        # How many distinct stimuli in each set
    sequence_id = 7                  # ID to log in sequence_info
    sequence_name = "Test Sequence Note"
    
    db_manager = DBManager()
    try:
        # 1) Connect to database
        engine = db_manager.connect()
        
        # 2) Get the list of resource IDs from the "resources" table for a given folder_path
        df_resources = db_manager.read_table("resources")
        df_filtered = df_resources.loc[df_resources["folder_paths"] == folder_path, "id"]
        stimuli_ids = df_filtered.tolist()

        if not stimuli_ids:
            print(f"No resources found in DB for folder path: {folder_path}")
            return

        # 3) Use our new logic to create the sets
        all_sets, leftover = create_sets_of_stimuli(stimuli_ids, repeats, set_size)
        
        if leftover:
            print("Warning: leftover items that could not form a complete set:", leftover)

        # 4) Build the DataFrame rows for our "sequences" table
        df_data = []
        for trial_idx, group in enumerate(all_sets):
            for order_idx, stim_id in enumerate(group):
                df_data.append([sequence_id, stim_id, trial_idx, order_idx])
        
        df_final = pd.DataFrame(df_data, columns=["sequence_id", "stimuli_id", "trial", "index_order"])
        
        print("Trial DataFrame (for 'sequences' table):")
        print(df_final)

        # 5) Insert a row into "sequence_info"
        df_sequence_info = pd.DataFrame([{
            "sequence_id": sequence_id,
            "sequence_name": sequence_name,
            "time_created": datetime.now(),  # current timestamp
            "folder_path": folder_path,
            "choice_set_size": set_size,
            # Instead of "n_trials", we can store how many sets were actually created
            "n_trials": len(all_sets)
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
