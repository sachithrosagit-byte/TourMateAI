import os
from run import app
from app.extensions import db
from app.models.uploaded_image import UploadedImage

with app.app_context():
    count = UploadedImage.query.count()
    UploadedImage.query.delete()
    db.session.commit()
    print(f"Deleted {count} uploaded images from the database.")
