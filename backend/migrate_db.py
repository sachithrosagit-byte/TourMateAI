import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST", "localhost")
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "")
db = os.getenv("DB_NAME", "tourmateai")

print(f"Connecting to MySQL on {host}")

conn = pymysql.connect(host=host, user=user, password=password, database=db)
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE Itineraries ADD COLUMN start_location VARCHAR(200);")
    cursor.execute("ALTER TABLE Itineraries ADD COLUMN end_location VARCHAR(200);")
    conn.commit()
    print("Added columns to MySQL")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
