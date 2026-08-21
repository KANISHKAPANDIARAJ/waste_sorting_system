import os
import cv2
import numpy as np
from PIL import Image

def allowed_file(filename, allowed_extensions):
    """Check if the file has a permitted extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def preprocess_image(image_path, target_size=(64, 64)):
    """
    Validates, loads, resizes, and normalizes an image.
    Returns:
        gray: Grayscale preprocessed image (target_size)
        color_rgb: RGB preprocessed image (target_size)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")

    # Load using OpenCV
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Invalid or corrupted image file.")

    # Convert to RGB (OpenCV loads as BGR)
    color_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Resize
    color_rgb_resized = cv2.resize(color_rgb, target_size, interpolation=cv2.INTER_AREA)
    gray_resized = cv2.resize(gray, target_size, interpolation=cv2.INTER_AREA)
    
    return gray_resized, color_rgb_resized

def extract_features(color_img, gray_img):
    """
    Extracts a feature vector from preprocessed images.
    Features:
        - Mean R, G, B (normalized 0-1)
        - Std Dev R, G, B (normalized 0-1)
        - Mean H, S, V (normalized 0-1)
        - Edge density (Canny edge detection ratio)
        - Mean grayscale gradient magnitude (texture roughness indicator)
    Returns:
        1D numpy array representing the feature vector
    """
    # 1. Color features (RGB)
    mean_rgb = np.mean(color_img, axis=(0, 1)) / 255.0
    std_rgb = np.std(color_img, axis=(0, 1)) / 255.0
    
    # 2. Color features (HSV)
    hsv_img = cv2.cvtColor(color_img, cv2.COLOR_RGB2HSV)
    mean_hsv = np.mean(hsv_img, axis=(0, 1))
    # Normalize HSV: H is 0-180 in OpenCV, S and V are 0-255
    mean_hsv[0] /= 180.0
    mean_hsv[1] /= 255.0
    mean_hsv[2] /= 255.0
    
    # 3. Shape/Edge features
    edges = cv2.Canny(gray_img, 50, 150)
    edge_density = np.sum(edges > 0) / float(gray_img.size)
    
    # 4. Texture features (Gradient magnitude standard dev)
    sobelx = cv2.Sobel(gray_img, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray_img, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobelx**2 + sobely**2)
    mean_gradient = np.mean(magnitude) / 255.0
    std_gradient = np.std(magnitude) / 255.0
    
    # Combine into a single feature vector
    features = np.concatenate([
        mean_rgb,        # 3 features
        std_rgb,         # 3 features
        mean_hsv,        # 3 features
        [edge_density],  # 1 feature
        [mean_gradient], # 1 feature
        [std_gradient]   # 1 feature
    ])
    
    return features
