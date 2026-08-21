import os
import sys

# Make project root importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import numpy as np
from PIL import Image
import tensorflow as tf

from ml.classifier import WasteClassifier


FILES = [
    "metal_0.png",
    "paper_0.png",
    "plastic_0.png",
    "organic_0.png",
    "other_0.png",
]

IMAGE_DIR = os.path.join(
    PROJECT_ROOT,
    "uploads",
    "waste",
    "train_samples"
)


classifier = WasteClassifier()

print("\n" + "=" * 70)
print("MOBILENETV2 RAW PREDICTION TEST")
print("=" * 70)

for filename in FILES:

    path = os.path.join(IMAGE_DIR, filename)

    print(f"\nIMAGE: {filename}")
    print(f"PATH : {path}")

    if not os.path.exists(path):
        print("ERROR: File does not exist")
        continue

    image = Image.open(path).convert("RGB")
    image = image.resize((224, 224))

    image_array = np.asarray(image, dtype=np.float32)
    image_array = np.expand_dims(image_array, axis=0)

    image_array = np.asarray(image, dtype=np.float32)
    image_array = np.expand_dims(image_array, axis=0)

    predictions = classifier.model.predict(
        image_array,
        verbose=0
    )[0]

    results = sorted(
        zip(classifier.class_names, predictions),
        key=lambda x: x[1],
        reverse=True
    )

    print("\nTop 5 predictions:")

    for class_name, probability in results[:5]:
        print(f"  {class_name:12s} : {probability:.4f}")

    print("\nClassifier result:")

    result = classifier.predict(path)

    print(f"  Material   : {result['material']}")
    print(f"  Raw class  : {result['raw_class']}")
    print(f"  Confidence : {result['confidence']}")
    print(f"  Index      : {result['class_index']}")

print("\n" + "=" * 70)