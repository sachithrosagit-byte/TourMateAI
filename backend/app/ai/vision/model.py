"""Model architecture for the landmark recognition CNN."""

import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Model

def build_model(num_classes: int) -> Model:
    """Builds a transfer learning model based on MobileNetV2.
    
    Args:
        num_classes: The number of distinct landmarks the model should recognize.
        
    Returns:
        An uncompiled Keras Model ready for training.
    """
    # Load the base model, pre-trained on ImageNet, without the top classification layer
    base_model = MobileNetV2(
        weights="imagenet", 
        include_top=False, 
        input_shape=(224, 224, 3)
    )
    
    # Unfreeze the top 20 layers of the base model for fine-tuning
    # This allows the model to learn specific features of Sri Lankan landmarks
    # instead of just relying on generic ImageNet features.
    base_model.trainable = True
    for layer in base_model.layers[:-20]:
        layer.trainable = False
    
    # Add our custom classification head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.2)(x)  # Prevent overfitting
    predictions = Dense(num_classes, activation="softmax")(x)
    
    # Construct the final model
    model = Model(inputs=base_model.input, outputs=predictions)
    
    return model
