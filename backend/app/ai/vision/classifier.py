"""Inference pipeline for landmark recognition."""

import json
import os
import io

from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from ...extensions import db
from ...models import Attraction

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "landmark_cnn.keras")
_CLASSES_PATH = os.path.join(os.path.dirname(__file__), "classes.json")

# Lazy-load so we don't block Flask startup, but cache across requests.
_model = None
_class_mapping = None

def _load_resources():
    """Load the trained model and class mapping JSON into memory."""
    global _model, _class_mapping
    
    if not os.path.exists(_MODEL_PATH) or not os.path.exists(_CLASSES_PATH):
        raise FileNotFoundError("Model or classes.json not found. Please run train.py first.")
        
    if _model is None:
        _model = tf.keras.models.load_model(_MODEL_PATH)
        
    if _class_mapping is None:
        with open(_CLASSES_PATH, "r") as f:
            _class_mapping = json.load(f)

def identify(image_file):
    """Predict the landmark from the uploaded image.
    
    Args:
        image_file: Werkzeug FileStorage object.
        
    Returns:
        dict: The recognition result shaped for `services.ai_service`.
    """
    try:
        _load_resources()
    except FileNotFoundError as e:
        # Fallback if the user hasn't trained the model yet
        return {
            "identified_name": "Unknown",
            "confidence": 0.0,
            "matched_attraction_id": None,
            "description": "The AI model has not been trained yet. Please train the model on the dataset.",
        }

    # 1. Read and preprocess the image
    img_bytes = image_file.read()
    image_file.seek(0) # Rewind the stream for saving later
    
    try:
        # MobileNetV2 expects 224x224 RGB images
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img)
        
        # Add batch dimension and scale pixels using MobileNet's preprocessor (-1 to 1)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
    except Exception:
        return {
            "identified_name": "Error",
            "confidence": 0.0,
            "matched_attraction_id": None,
            "description": "Could not read or process the uploaded image file.",
        }

    # 2. Run inference
    predictions = _model.predict(img_array)[0]
    
    # 3. Find top prediction
    predicted_index = np.argmax(predictions)
    confidence = float(predictions[predicted_index])
    
    # 4. Map index back to database Attraction
    folder_name = _class_mapping.get(str(predicted_index))
    if not folder_name:
        return {
            "identified_name": "Unknown",
            "confidence": confidence,
            "matched_attraction_id": None,
            "description": "Recognized a shape, but it's not mapped to a known attraction.",
        }
        
    # The folder name is used in the dataset. Let's try to match it against the DB.
    # Convert "Sigiriya_Rock_Fortress" to a likely matching format if needed, 
    # but the safest is to find the attraction by exact or partial match.
    search_term = folder_name.replace("_", " ")
    
    # Simple ILIKE search in the DB
    attraction = Attraction.query.filter(Attraction.name.ilike(f"%{search_term}%")).first()
    
    if attraction:
        # Confidence threshold: if it's too low, we don't confirm it.
        # Given it's a small dataset, we'll use a conservative threshold.
        if confidence > 0.5:
            return {
                "identified_name": attraction.name,
                "confidence": confidence,
                "matched_attraction_id": attraction.id,
                "description": attraction.description,
            }
        else:
            return {
                "identified_name": "Unknown (Low Confidence)",
                "confidence": confidence,
                "matched_attraction_id": None,
                "description": f"The model thought this might be {attraction.name}, but wasn't sure.",
            }
            
    # If the DB doesn't have it (e.g. folder name doesn't match DB well)
    return {
        "identified_name": search_term.title(),
        "confidence": confidence,
        "matched_attraction_id": None,
        "description": "Recognized the landmark, but could not link it to the database.",
    }
