import os
import re
import pandas as pd
import gdown
import zipfile
from database_utils import DBManager

# =============================================================================
# 1. Set up the ZIP file download link.
# You have two options:
# Option A: Use a direct download link (recommended) in the format:
#    "https://drive.google.com/uc?id=FILE_ID"
# Option B: Use the original view link and enable fuzzy mode.
#
# Uncomment the option you prefer:
# -----------------------------------------------------------------------------
# Option A: Direct download URL (ensure this file is a valid ZIP file)
zip_link = "https://drive.google.com/uc?export=download&id=1S_G65KqPVLgtXZzTo019jPAzs41_0_4y"
# -----------------------------------------------------------------------------
# Option B: Original view URL with fuzzy mode enabled:
# zip_link = "https://drive.google.com/file/d/1S_G65KqPVLgtXZzTo019jPAzs41_0_4y/view?usp=sharing"
# =============================================================================

# Hardcode folder name (used in DB records / local storage)
folder_name = "Guitar"

# Build the destination directory path for extraction
destination_dir = os.path.join("..", "www-react", "backend", "static", folder_name)
os.makedirs(destination_dir, exist_ok=True)

# Temporary path for the downloaded ZIP file
local_zip_path = os.path.join(destination_dir, "temp_download.zip")

# =============================================================================
# 2. Download the ZIP file via gdown
# Enable fuzzy mode to help parse the URL if needed.
# =============================================================================
print("Downloading ZIP archive from Google Drive...")
gdown.download(url=zip_link, output=local_zip_path, quiet=False, fuzzy=True)

# (Optional) Print the downloaded file size for debugging purposes
print("Downloaded file size (bytes):", os.path.getsize(local_zip_path))

# =============================================================================
# 3. Validate and extract the ZIP file
# =============================================================================
try:
    with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
        print("Extracting ZIP archive...")
        zip_ref.extractall(destination_dir)
except zipfile.BadZipFile:
    print("Error: The downloaded file is not a valid ZIP file. Please check the URL and ensure it points to a ZIP file.")
    exit(1)

# Remove the temporary ZIP file after extraction
os.remove(local_zip_path)

# =============================================================================
# 4. Prepare records for the database by scanning the destination directory
# =============================================================================
records = []
for root, dirs, files in os.walk(destination_dir):
    for file in files:
        # Construct a relative path: e.g., "resources/Guitar/<filename>"
        rel_path = os.path.join("resources", folder_name, file)
        description = "File downloaded from public Google Drive folder to static directory"
        records.append((file, rel_path, description))

if not records:
    print("No files found after unzipping.")
    exit(0)

# Convert the records list to a DataFrame
df_records = pd.DataFrame(records, columns=["filenames", "folder_paths", "descriptions"])

# =============================================================================
# 5. Insert the records into the database
# =============================================================================
db_manager = DBManager()
engine = db_manager.connect()
try:
    db_manager.append_table("resources", df_records)
    print("Files inserted successfully into the database.")
except Exception as e:
    print("Error inserting files into the database:", e)
finally:
    db_manager.close()
