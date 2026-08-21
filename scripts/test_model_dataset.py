from pathlib import Path
import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model

DATASET_DIR = Path(r"D:\archive\standardized_256")
MODEL_PATH = Path(r"ml\models\waste_mobilenetv2.keras")

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
IMAGES_PER_CLASS = 100

CLASS_NAMES = [
    "battery",
    "biological",
    "cardboard",
    "clothes",
    "glass",
    "metal",
    "paper",
    "plastic",
    "shoes",
    "trash"
]

print("=" * 70)
print("MOBILENETV2 QUICK DATASET DIAGNOSTIC")
print("=" * 70)

# --------------------------------------------------
# Load dataset
# --------------------------------------------------

dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    labels="inferred",
    label_mode="int",
    class_names=CLASS_NAMES,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True,
    seed=42
)

print("\nTensorFlow class order:")
print(dataset.class_names)

# --------------------------------------------------
# Limit dataset
# --------------------------------------------------

max_images = IMAGES_PER_CLASS * len(CLASS_NAMES)

dataset = dataset.take(
    (max_images + BATCH_SIZE - 1) // BATCH_SIZE
)

print(f"\nTesting approximately {max_images} images...")
print("This should be much faster than testing all 12,259 images.\n")

# --------------------------------------------------
# Load model
# --------------------------------------------------

print("Loading MobileNetV2 model...")

model = load_model(MODEL_PATH)

print("✅ Model loaded.\n")

# --------------------------------------------------
# Prediction
# --------------------------------------------------

true_labels = []
pred_labels = []

batch_number = 0

for images, labels in dataset:

    batch_number += 1

    print(
        f"Processing batch {batch_number}...",
        end="\r"
    )

    predictions = model.predict(
        images,
        verbose=0
    )

    predicted_classes = np.argmax(
        predictions,
        axis=1
    )

    true_labels.extend(labels.numpy())
    pred_labels.extend(predicted_classes)

true_labels = np.array(true_labels)
pred_labels = np.array(pred_labels)

print("\n")

# --------------------------------------------------
# Overall accuracy
# --------------------------------------------------

accuracy = np.mean(
    true_labels == pred_labels
)

print("=" * 70)
print(
    f"OVERALL ACCURACY: {accuracy * 100:.2f}%"
)
print("=" * 70)

# --------------------------------------------------
# Per-class accuracy
# --------------------------------------------------

print("\nPER-CLASS ACCURACY")
print("-" * 70)

for i, class_name in enumerate(CLASS_NAMES):

    mask = true_labels == i

    total = np.sum(mask)

    if total == 0:
        continue

    correct = np.sum(
        pred_labels[mask] == i
    )

    class_accuracy = (
        correct / total * 100
    )

    print(
        f"{class_name:<15}"
        f"{correct:>5}/{total:<5}"
        f"{class_accuracy:>7.2f}%"
    )

# --------------------------------------------------
# Prediction distribution
# --------------------------------------------------

print("\nPREDICTION DISTRIBUTION")
print("-" * 70)

for i, class_name in enumerate(CLASS_NAMES):

    count = np.sum(
        pred_labels == i
    )

    percentage = (
        count / len(pred_labels) * 100
    )

    print(
        f"{class_name:<15}"
        f"{count:>6}"
        f" ({percentage:>6.2f}%)"
    )

# --------------------------------------------------
# Confusion matrix
# --------------------------------------------------

print("\nCONFUSION MATRIX")
print("-" * 70)

cm = tf.math.confusion_matrix(
    true_labels,
    pred_labels,
    num_classes=len(CLASS_NAMES)
).numpy()

print("\nRows = Actual")
print("Columns = Predicted\n")

print(
    " " * 15 +
    " ".join(
        f"{name[:7]:>8}"
        for name in CLASS_NAMES
    )
)

for i, row in enumerate(cm):

    print(
        f"{CLASS_NAMES[i]:<15}" +
        " ".join(
            f"{x:>8}"
            for x in row
        )
    )

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)