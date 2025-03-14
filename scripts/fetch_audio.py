import os
import urllib.parse
import pandas as pd
from database_utils import DBManager

# ---------------------------------------------------------------------------
# 1. Define paths and S3 base URL
# ---------------------------------------------------------------------------
# Path to your text file containing the list of file names.
txt_file_path = r"audio.txt"  # Update this with your actual file path

# Define your S3 base URL.
s3_base_url = "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Guitar/"

def get_s3_link(filename, base_url=s3_base_url):
    """
    Convert a file name into an S3 URL.
    - Ensures the filename ends with '.wav'
    - URL-encodes the filename (e.g., spaces become '+')
    """
    filename = filename.strip()
    if not filename.lower().endswith(".wav"):
        filename += ".wav"
    encoded_filename = urllib.parse.quote_plus(filename)
    return base_url + encoded_filename

# ---------------------------------------------------------------------------
# 2. Load the file list from the text file
# ---------------------------------------------------------------------------
try:
    with open(txt_file_path, 'r') as file:
        content = file.read()
except FileNotFoundError:
    print(f"Error: File not found at {txt_file_path}")
    exit(1)

# Assume the file names are comma-separated
file_names = [item.strip() for item in content.split(',') if item.strip()]

if not file_names:
    print("No file names found in the text file.")
    exit(0)

# ---------------------------------------------------------------------------
# 3. Prepare records for the database
# ---------------------------------------------------------------------------
records = []
for file in file_names:
    s3_link = get_s3_link(file)
    description = "File mapped to S3 URL from text file"
    # Here, we use 'folder_paths' to store the S3 URL.
    records.append((file, s3_link, description))

# Convert the records list to a DataFrame
df_records = pd.DataFrame(records, columns=["filenames", "folder_paths", "descriptions"])

# ---------------------------------------------------------------------------
# 4. Insert the records into the database
# ---------------------------------------------------------------------------
db_manager = DBManager()
engine = db_manager.connect()
try:
    db_manager.append_table("resources", df_records)
    print("Files inserted successfully into the database.")
except Exception as e:
    print("Error inserting files into the database:", e)
finally:
    db_manager.close()
