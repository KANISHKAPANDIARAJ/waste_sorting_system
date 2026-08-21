import os
import sys
import pytest
import cv2
import numpy as np

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.preprocessing import preprocess_image, extract_features
from ml.classifier import WasteClassifier

@pytest.fixture
def mock_image_path():
    """Generates a temporary blue image representing plastic for classifier validation."""
    img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratch')
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, 'test_specimen.png')
    
    # Create blue matrix
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :] = (200, 20, 20)  # BGR Blue
    cv2.imwrite(img_path, img)
    
    yield img_path
    
    # Cleanup
    if os.path.exists(img_path):
        os.remove(img_path)

def test_preprocessing(mock_image_path):
    """Verify loading and sizing metrics."""
    gray, color = preprocess_image(mock_image_path, target_size=(64, 64))
    assert gray.shape == (64, 64)
    assert color.shape == (64, 64, 3)

def test_feature_extraction(mock_image_path):
    """Verify extraction dimension match."""
    gray, color = preprocess_image(mock_image_path, target_size=(64, 64))
    features = extract_features(color, gray)
    assert len(features) == 12  # Mean RGB (3), Std RGB (3), Mean HSV (3), Canny (1), Grad Mean (1), Grad Std (1)

def test_classifier_prediction(mock_image_path):
    """Verify prediction return schema."""
    classifier = WasteClassifier()
    res = classifier.predict(mock_image_path)
    
    assert 'material' in res
    assert 'confidence' in res
    assert 'processing_time' in res
    assert 'model_version' in res
    assert res['confidence'] >= 0.0 and res['confidence'] <= 1.0
