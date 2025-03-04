import pandas as pd
import time
from database_utils import DBManager

# Instantiate DBManager and connect to the database
db_manager = DBManager()
engine = db_manager.connect()


df = db_manager.read_table("resources")

# Print the DataFrame with all rows and columns nicely formatted
print(df.to_string(index=False))

# Optional pause before closing the connection
time.sleep(1)
db_manager.close()

    

    