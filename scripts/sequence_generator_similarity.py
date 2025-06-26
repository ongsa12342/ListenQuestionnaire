import pandas as pd
import random
import time
from datetime import datetime
from database_utils import DBManager


def main():
    # For demonstration purposes, adjust these as needed:
    folder_path = r"https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/GuitarSimilarity/"   # This matches what's in your DB
    sequence_id = 8                  # ID to log in sequence_info
    sequence_name = "Similarity"
    
    db_manager = DBManager()
    try:
        # 1) Connect to database
        engine = db_manager.connect()
        
        # 2) Get the list of resource IDs from the "resources" table for a given folder_path
        df_resources = db_manager.read_table("resources")
        df_resources["folder_paths"] = df_resources["folder_paths"].str.replace("\\", "/", regex=False)
        df_filtered = df_resources[df_resources["folder_paths"].str.startswith(folder_path)]
        # stimuli_ids = df_filtered.tolist()

        # if not stimuli_ids:
        #     print(f"No resources found in DB for folder path: {folder_path}")
        #     return
        # print(df_filtered)

        # Extract prefix/group (e.g., "Classic", "Country", etc.)
        df_filtered["group"] = df_filtered["filenames"].str.extract(r"^([A-Za-z0-9]+)_")


        # Group by prefix
        all_trials = []
        trial_counter = 0

        for group_name, group_df in df_filtered.groupby("group"):
            if len(group_df) < 4:
                continue  # skip incomplete groups

            group_df = group_df.sort_values("filenames")  # optional: for consistent order

            # Assign anchor (e.g., index_order = 0)
            ref_row = group_df.iloc[0]
            print(ref_row["filenames"], ref_row["id"])


            # Randomize other 3 stimuli order
            other_stimuli = group_df.sample(frac=1).reset_index(drop=True)
            
            # Build trial rows
            trial_rows = []
            trial_rows.append({
                "sequence_id": sequence_id,
                "stimuli_id": ref_row["id"],
                "trial": trial_counter,
                "index_order": 0
            })
            
            for idx, row in other_stimuli.iterrows():
                trial_rows.append({
                    "sequence_id": sequence_id,
                    "stimuli_id": row["id"],
                    "trial": trial_counter,
                    "index_order": idx + 1
                })

            trial_counter += 1
            all_trials.extend(trial_rows)

        # Convert to DataFrame
        df_final = pd.DataFrame(all_trials, columns=["sequence_id", "stimuli_id", "trial", "index_order"])

        # Calculate number of trials based on unique groups
        n_trials = df_final["trial"].nunique()  # OR use len(set of group names)

        # Build one-row DataFrame for sequence info
        df_sequence_info = pd.DataFrame([{
            "sequence_id": sequence_id,
            "sequence_name": sequence_name,
            "time_created": datetime.now(),
            "folder_path": folder_path,
            "choice_set_size": 4,
            "n_trials": n_trials
        }])

        # import code ; code.interact(local=locals())

        # # 3) Use our new logic to create the sets
        # all_sets, leftover = create_sets_of_stimuli(stimuli_ids, repeats, set_size)
        
        # if leftover:
        #     print("Warning: leftover items that could not form a complete set:", leftover)

        # # 4) Build the DataFrame rows for our "sequences" table
        # df_data = []
        # for trial_idx, group in enumerate(all_sets):
        #     for order_idx, stim_id in enumerate(group):
        #         df_data.append([sequence_id, stim_id, trial_idx, order_idx])
        
        # df_final = pd.DataFrame(df_data, columns=["sequence_id", "stimuli_id", "trial", "index_order"])
        
        # print("Trial DataFrame (for 'sequences' table):")
        # print(df_final)

        # # 5) Insert a row into "sequence_info"
        # df_sequence_info = pd.DataFrame([{
        #     "sequence_id": sequence_id,
        #     "sequence_name": sequence_name,
        #     "time_created": datetime.now(),  # current timestamp
        #     "folder_path": folder_path,
        #     "choice_set_size": set_size,
        #     # Instead of "n_trials", we can store how many sets were actually created
        #     "n_trials": len(all_sets)
        # }])
        
        # print("\nSequence Info DataFrame (for 'sequence_info' table):")
        # print(df_sequence_info)

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
