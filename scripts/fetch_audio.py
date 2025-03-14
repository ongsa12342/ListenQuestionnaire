import os
import re
import pandas as pd
import gdown
from database_utils import DBManager

# Public Google Drive folder link
folder_link = "https://drive.google.com/drive/folders/1CH7arPsru4ejyj_Wm7dlPY0Np60YJeI7?usp=sharing"

# Extract the folder ID from the URL using regex (still needed for gdown)
match = re.search(r'folders/([^?]+)', folder_link)
if match:
    folder_id = match.group(1)
else:
    print("Invalid folder link provided!")
    exit(1)

# Hardcode folder name as "piano"
folder_name = "Guitar"

# Build the destination directory path (downloading into backend static folder)
destination_dir = os.path.join("..", "www-react", "backend", "static", folder_name)
os.makedirs(destination_dir, exist_ok=True)

# Download the folder using gdown (public link, no authentication needed)
print("Downloading folder from Google Drive...")
gdown.download_folder(folder_link, output=destination_dir, use_cookies=False)

# Scan the destination directory for files and prepare records for the database
records = []
for root, dirs, files in os.walk(destination_dir):
    for file in files:
        # Construct a relative path: "static/piano/<filename>"
        rel_path = os.path.join("resources", folder_name, file)
        description = "File downloaded from public Google Drive folder to static directory"
        records.append((file, rel_path, description))

if not records:
    print("No files found in the destination directory.")
    exit(0)

# Convert the records list to a DataFrame
df_records = pd.DataFrame(records, columns=["filenames", "folder_paths", "descriptions"])

# Update the database
db_manager = DBManager()
engine = db_manager.connect()
try:
    db_manager.append_table("resources", df_records)
    print("Files inserted successfully into the database.")
except Exception as e:
    print("Error inserting files into the database:", e)
finally:
    db_manager.close()
