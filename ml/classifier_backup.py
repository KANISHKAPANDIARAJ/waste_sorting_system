import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from ml.preprocessing import preprocess_image, extract_features

# Supported waste categories
CATEGORIES = ['Plastic', 'Paper', 'Metal', 'Organic', 'Other']

# Path to the serialized model file
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, 'models', 'waste_classifier.pkl')

class WasteClassifier:
    def __init__(self):
        self.model = None
        self.model_version = "v1.0"
        self.load_model()
        
    def load_model(self):
        """Attempts to load the pre-trained classifier model."""
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"Loaded classifier model from {MODEL_PATH}")
            except Exception as e:
                print(f"Error loading model: {e}. Falling back to heuristic classifier.")
                self.model = None
        else:
            print(f"No trained model found at {MODEL_PATH}. Falling back to heuristic classifier.")
            self.model = None

    def train(self, X_train, y_train):
        """
        Trains the Random Forest model and saves it.
        X_train: list/array of feature vectors
        y_train: list/array of labels (string names or indices)
        """
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        
        # Fit Random Forest
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Save model
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(self.model, f)
        
        print(f"Model successfully trained and saved to {MODEL_PATH}")

    def predict(self, image_path):
        """
        Runs the full classification pipeline:
        Preprocessing -> Feature Extraction -> Inference -> Result
        """
        import time
        start_time = time.time()
        
        try:
            # Preprocess and extract features
            gray_img, color_img = preprocess_image(image_path)
            features = extract_features(color_img, gray_img)
            
            # Predict using model if loaded
            if self.model is not None:
                features_reshaped = features.reshape(1, -1)
                pred_class = self.model.predict(features_reshaped)[0]
                probs = self.model.predict_proba(features_reshaped)[0]
                
                # Find class index and confidence
                class_idx = list(self.model.classes_).index(pred_class)
                confidence = float(probs[class_idx])
            else:
                # Use rule-based fallback heuristics based on extracted features
                pred_class, confidence = self._heuristic_predict(features, image_path)
                
        except Exception as e:
            # Never invent a class from the filename or a random/hash value.
            # A failed image/model inference must be surfaced to the API.
            print(f"Classification error: {e}")
            raise ValueError(f"Unable to classify image: {e}") from e
            
        processing_time = time.time() - start_time
        
        return {
            'material': pred_class,
            'confidence': round(confidence, 3),
            'processing_time': round(processing_time, 4),
            'model_version': self.model_version
        }

    def _heuristic_predict(self, features, image_path):
        """
        A heuristic classifier based on extracted features:
        [mean_r, mean_g, mean_b, std_r, std_g, std_b, mean_h, mean_s, mean_v, edge_density, mean_grad, std_grad]
        """
        mean_r, mean_g, mean_b = features[0], features[1], features[2]
        mean_h, mean_s, mean_v = features[6], features[7], features[8]
        edge_density = features[9]
        
        # Simple colors/edge classification rules
        # High green -> Organic
        if mean_g > mean_r and mean_g > mean_b and mean_g > 0.4:
            pred_class = 'Organic'
            confidence = 0.72 + (mean_g - mean_r) * 0.5
        # High grey/metallic, high edges -> Metal
        elif edge_density > 0.15 and abs(mean_r - mean_b) < 0.05 and abs(mean_g - mean_b) < 0.05:
            pred_class = 'Metal'
            confidence = 0.75 + min(edge_density * 0.5, 0.2)
        # Clear/blue -> Plastic
        elif mean_b > mean_r and mean_b > 0.4:
            pred_class = 'Plastic'
            confidence = 0.70 + (mean_b - mean_r) * 0.4
        # High intensity white/light brown -> Paper
        elif mean_v > 0.6 and (0.05 < mean_h < 0.15):  # Hue matches brown/beige
            pred_class = 'Paper'
            confidence = 0.68 + (mean_v - 0.6) * 0.5
        else:
            # Unknown visual pattern: do not fabricate a confident class.
            pred_class = 'Other'
            confidence = 0.50

        return pred_class, min(confidence, 0.99)
