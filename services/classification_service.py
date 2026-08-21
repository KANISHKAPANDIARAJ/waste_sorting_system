from ml.classifier import WasteClassifier

# Instantiate a single, shared classifier instance (Singleton pattern)
classifier = WasteClassifier()

def classify_waste_image(image_path):
    """
    Accepts path to a waste image, validates and preprocesses it,
    runs model inference, and returns prediction details.
    """
    return classifier.predict(image_path)

def retrain_classifier(X_train, y_train):
    """
    Retrains the underlying ML classifier with new samples
    and saves the model parameter file.
    """
    classifier.train(X_train, y_train)
    # Reload model to ensure updates are live
    classifier.load_model()
