"""Training pipeline for the landmark recognition CNN."""

import json
import os

import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import RandomFlip, RandomRotation, RandomZoom, Input
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from .model import build_model

# Configuration
_DATASET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/dataset"))
_MODEL_SAVE_PATH = os.path.join(os.path.dirname(__file__), "landmark_cnn.keras")
_CLASSES_SAVE_PATH = os.path.join(os.path.dirname(__file__), "classes.json")

BATCH_SIZE = 32
IMG_SIZE = (224, 224)
EPOCHS = 30  # Good amount for ~300 images

def get_data_augmentation():
    """Returns a sequential model containing augmentation layers."""
    return Sequential([
        Input(shape=(224, 224, 3)),
        RandomFlip("horizontal"),
        RandomRotation(0.2),  # Increased slightly again since we have more data
        RandomZoom(0.2),
    ], name="data_augmentation")

def train():
    """Trains the CNN on the dataset and saves the model."""
    if not os.path.exists(_DATASET_DIR) or not os.listdir(_DATASET_DIR):
        print(f"Error: No dataset found at {_DATASET_DIR}")
        return

    print("Loading dataset...")
    
    # Load training data
    train_ds = tf.keras.utils.image_dataset_from_directory(
        _DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
    )
    
    # Load validation data
    val_ds = tf.keras.utils.image_dataset_from_directory(
        _DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Found {num_classes} classes: {class_names}")

    # Save class mapping
    class_mapping = {str(i): name for i, name in enumerate(class_names)}
    with open(_CLASSES_SAVE_PATH, "w") as f:
        json.dump(class_mapping, f, indent=2)
    print(f"Saved class mapping to {_CLASSES_SAVE_PATH}")

    # Preprocess inputs for MobileNetV2 (scales pixels to [-1, 1])
    train_ds = train_ds.map(lambda x, y: (preprocess_input(x), y))
    val_ds = val_ds.map(lambda x, y: (preprocess_input(x), y))

    # Apply data augmentation only to training data
    data_augmentation = get_data_augmentation()
    train_ds = train_ds.map(lambda x, y: (data_augmentation(x, training=True), y))

    # Optimize datasets for performance
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    print("Building model architecture...")
    model = build_model(num_classes)
    
    model.compile(
        optimizer=Adam(learning_rate=1e-4),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"]
    )

    # Callbacks
    callbacks = [
        EarlyStopping(patience=10, restore_best_weights=True, monitor="val_loss"),
        ModelCheckpoint(_MODEL_SAVE_PATH, save_best_only=True, monitor="val_loss")
    ]

    print("Starting training...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks
    )

    print(f"Training complete! Best model saved to {_MODEL_SAVE_PATH}")
    
    # Evaluate final model
    loss, accuracy = model.evaluate(val_ds)
    print(f"Final Validation Accuracy: {accuracy*100:.2f}%")

if __name__ == "__main__":
    train()
