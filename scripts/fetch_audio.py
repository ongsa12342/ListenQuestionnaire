import os
import re
import pandas as pd
import gdown
import zipfile
from database_utils import DBManager

# =============================================================================
# 1. Define the ZIP file's public link from Google Drive
#    *IMPORTANT*: Use the "uc?id=<FILE_ID>" direct download format
# =============================================================================
# Example share link format: https://drive.google.com/uc?id=1yAXXXXXX1234XXXXX
# Replace with your actual ZIP file link:
zip_link = "https://drive.google.com/file/d/1S_G65KqPVLgtXZzTo019jPAzs41_0_4y/view?usp=sharing"

# Hardcode folder name (used in DB records / local storage)
folder_name = "Guitar"

# =============================================================================
# 2. Build the destination directory path for extraction
# =============================================================================
destination_dir = os.path.join("..", "www-react", "backend", "static", folder_name)
os.makedirs(destination_dir, exist_ok=True)

# A path to temporarily store the downloaded ZIP before extracting
local_zip_path = os.path.join(destination_dir, "temp_download.zip")

# =============================================================================
# 3. Download the ZIP file via gdown
# =============================================================================
print("Downloading ZIP archive from Google Drive...")
gdown.download(url=zip_link, output=local_zip_path, quiet=False)

# =============================================================================
# 4. Extract the ZIP into our destination directory
# =============================================================================
print("Extracting ZIP archive...")
with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
    zip_ref.extractall(destination_dir)

# (Optional) Remove the ZIP file after extraction
os.remove(local_zip_path)

# =============================================================================
# 5. Build up the list of (filename, relative_path, description) for the DB
# =============================================================================
records = []
for root, dirs, files in os.walk(destination_dir):
    for file in files:
        # Construct a relative path if you want to store it that way in DB
        rel_path = os.path.join("resources", folder_name, file)
        description = "File downloaded from public Google Drive folder to static directory"
        records.append((file, rel_path, description))

# =============================================================================
# 6. Insert records into the database
# =============================================================================
if not records:
    print("No files found after unzipping.")
else:
    df_records = pd.DataFrame(records, columns=["filenames", "folder_paths", "descriptions"])
    db_manager = DBManager()
    engine = db_manager.connect()
    try:
        db_manager.append_table("resources", df_records)
        print("Files inserted successfully into the database.")
    except Exception as e:
        print("Error inserting files into the database:", e)
    finally:
        db_manager.close()
