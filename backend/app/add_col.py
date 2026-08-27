import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from run import app
from app.extensions import db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE Itineraries ADD COLUMN description TEXT;"))
        db.session.commit()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error: {e}")
