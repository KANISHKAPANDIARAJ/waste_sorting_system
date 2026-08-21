import os
import json
import time
import numpy as np
import tensorflow as tf
from PIL import Image


# ============================================================
# APPLICATION CATEGORIES
# ============================================================

CATEGORIES = [
    'Plastic',
    'Paper',
    'Metal',
    'Organic',
    'Other'
]


# ============================================================
# MODEL PATHS
# ============================================================

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    MODEL_DIR,
    'models',
    'waste_mobilenetv2.keras'
)

CLASS_NAMES_PATH = os.path.join(
    MODEL_DIR,
    'models',
    'waste_class_names.json'
)


# ============================================================
# MODEL → APPLICATION CATEGORY MAPPING
# ============================================================

CLASS_MAPPING = {
    'plastic': 'Plastic',
    'paper': 'Paper',
    'cardboard': 'Paper',
    'metal': 'Metal',
    'biological': 'Organic',
    'glass': 'Other',
    'battery': 'Other',
    'clothes': 'Other',
    'shoes': 'Other',
    'trash': 'Other'
}


# ============================================================
# IMAGE CONFIGURATION
# ============================================================

IMAGE_SIZE = (224, 224)


# ============================================================
# WASTE CLASSIFIER
# ============================================================

class WasteClassifier:

    def __init__(self):
        self.model = None
        self.class_names = []
        self.model_version = "MobileNetV2-v2.0"

        self.load_model()

    # ========================================================
    # LOAD MODEL
    # ========================================================

    def load_model(self):
        """Load the trained MobileNetV2 model and class names."""

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"MobileNetV2 model not found at: {MODEL_PATH}"
            )

        if not os.path.exists(CLASS_NAMES_PATH):
            raise FileNotFoundError(
                f"Class names file not found at: {CLASS_NAMES_PATH}"
            )

        try:

            print(
                f"Loading MobileNetV2 model from: {MODEL_PATH}"
            )

            self.model = tf.keras.models.load_model(
                MODEL_PATH
            )

            with open(
                CLASS_NAMES_PATH,
                'r'
            ) as f:

                self.class_names = json.load(f)

            print(
                f"Loaded {len(self.class_names)} waste classes:"
            )

            print(
                self.class_names
            )

            print(
                "MobileNetV2 model loaded successfully."
            )

        except Exception as e:

            self.model = None

            print(
                f"Error loading MobileNetV2 model: {e}"
            )

            raise RuntimeError(
                f"Unable to load waste classification model: {e}"
            ) from e

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict(self, image_path):
        """
        Runs MobileNetV2 image classification.

        Pipeline:
        Image
        → RGB
        → Resize 224x224
        → MobileNetV2 preprocessing
        → Model prediction
        → Dataset class
        → Application category
        """

        start_time = time.time()

        if self.model is None:
            raise RuntimeError(
                "Waste classification model is not loaded."
            )

        try:

            # ------------------------------------------------
            # Load image
            # ------------------------------------------------

            image = Image.open(
                image_path
            ).convert(
                'RGB'
            )

            # ------------------------------------------------
            # Resize exactly to training dimensions
            # ------------------------------------------------

            image = image.resize(
                IMAGE_SIZE
            )

            # ------------------------------------------------
            # Convert image to NumPy array
            # ------------------------------------------------

            image_array = np.asarray(
                image,
                dtype=np.float32
            )

            # ------------------------------------------------
            # Add batch dimension
            # Shape:
            # (224, 224, 3)
            # →
            # (1, 224, 224, 3)
            # ------------------------------------------------

            image_array = np.expand_dims(
                image_array,
                axis=0
            )

            # ------------------------------------------------
            # IMPORTANT:
            # Same preprocessing used during training
            # ------------------------------------------------


            # ------------------------------------------------
            # Run model prediction
            # ------------------------------------------------

            predictions = self.model.predict(
                image_array,
                verbose=0
            )

            probabilities = predictions[0]

            # ------------------------------------------------
            # Get highest probability class
            # ------------------------------------------------

            class_index = int(
                np.argmax(probabilities)
            )

            raw_class = self.class_names[
                class_index
            ]

            confidence = float(
                probabilities[class_index]
            )

            # ------------------------------------------------
            # Map dataset class to application category
            # ------------------------------------------------

            material = CLASS_MAPPING.get(
                raw_class.lower(),
                'Other'
            )

            processing_time = (
                time.time() - start_time
            )

            # ------------------------------------------------
            # Return same structure expected by API
            # ------------------------------------------------

            return {
                'material': material,
                'confidence': round(
                    confidence,
                    3
                ),
                'processing_time': round(
                    processing_time,
                    4
                ),
                'model_version': self.model_version,

                # Extra information useful for
                # debugging/dashboard
                'raw_class': raw_class,
                'class_index': class_index
            }

        except Exception as e:

            print(
                f"Classification error: {e}"
            )

            raise ValueError(
                f"Unable to classify image: {e}"
            ) from e

    # ========================================================
    # TRAIN METHOD
    # ========================================================

    def train(self, X_train, y_train):
        """
        Training is handled by the dedicated MobileNetV2
        training script.

        This method is retained for compatibility with the
        existing classification service.
        """

        raise NotImplementedError(
            "Training is handled by the MobileNetV2 "
            "training script. Run the training script "
            "to retrain the model."
        )