import os
import boto3
import pandas as pd
from database_utils import DBManager

# S3 bucket and prefix
bucket_name = "dataset-guitar"
prefix = "Guitar/"  # s3://dataset-guitar/Guitar/

# Hardcode folder name used in the DB record
folder_name = "Guitar"
description = "S3 file reference (no local download)"

# Initialize S3 client
s3 = boto3.client("s3")

# 1. List objects in the specified S3 bucket and prefix
objects_response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
if "Contents" not in objects_response:
    print(f"No objects found at s3://{bucket_name}/{prefix}")
    exit(0)

records = []
for obj in objects_response["Contents"]:
    key = obj["Key"]
    # Skip "directory" placeholders ending with "/"
    if key.endswith("/"):
        continue

    # Example: if "Guitar/some-file.jpg", then:
    #   filename = "some-file.jpg"
    filename = os.path.basename(key)

    # For the folder_path, you might store a full S3 URL, 
    # or just a relative path. Choose whichever suits your needs.
    #
    # Option A: store full S3 URL
    # folder_path = f"s3://{bucket_name}/{key}"
    #
    # Option B: store just the key
    # folder_path = key
    #
    # Option C: mimic your original scheme (e.g. "resources/Guitar/myfile.jpg")
    folder_path = os.path.join("resources", folder_name, filename)

    records.append((filename, folder_path, description))

# If no objects after skipping directories
if not records:
    print(f"No files found under prefix {prefix}.")
    exit(0)

# 2. Convert to DataFrame
df_records = pd.DataFrame(records, columns=["filenames", "folder_paths", "descriptions"])

# 3. Insert the records into the database
db_manager = DBManager()
engine = db_manager.connect()
try:
    db_manager.append_table("resources", df_records)
    print("Files inserted successfully into the database.")
except Exception as e:
    print("Error inserting files into the database:", e)
finally:
    db_manager.close()
