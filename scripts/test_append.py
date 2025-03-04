import os
import pandas as pd
import time
from database_utils import DBManager

# Prompt the user to enter a folder path
folder_path = input("Enter folder path: ")

# Verify that the provided path is a directory
if not os.path.isdir(folder_path):
    print("Invalid folder path provided!")
    exit(1)

# List all entries in the folder and prepare records for insertion
records = []
for entry in os.listdir(folder_path):
    full_path = os.path.join(folder_path, entry)
    # Only consider files (not subdirectories)
    if os.path.isfile(full_path):
        description = "File added from folder scanning"
        records.append((entry, folder_path, description))

if not records:
    print("No files found in the provided folder.")
    exit(0)

# Convert the list of records to a DataFrame
df_records = pd.DataFrame(records, columns=["filenames", "folder_paths", "descriptions"])

if not records:
    print("No files found in the provided folder.")
    exit(0)

# Instantiate DBManager and connect to the database
db_manager = DBManager()
engine = db_manager.connect()

try:
    db_manager.append_table("resources",df_records)
    print("Files inserted successfully.")
except Exception as e:
    print("Error inserting files:", e)


db_manager.close()
