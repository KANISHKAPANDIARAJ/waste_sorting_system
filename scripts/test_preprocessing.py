import os
import numpy as np
import tensorflow as tf
from PIL import Image

MODEL_PATH = r"ml\models\waste_mobilenetv2.keras"

IMAGE_PATH = (
    r"D:\archive\standardized_256\paper\paper_1152.jpg"
)

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

IMAGE_SIZE = (224, 224)


print("=" * 80)
print("MOBILENETV2 PREPROCESSING COMPARISON")
print("=" * 80)

print("\nModel:")
print(os.path.abspath(MODEL_PATH))

print("\nImage:")
print(IMAGE_PATH)


# ------------------------------------------------------------
# Load model
# ------------------------------------------------------------

model = tf.keras.models.load_model(
    MODEL_PATH
)

print("\n✅ Model loaded")


# ------------------------------------------------------------
# Load image
# ------------------------------------------------------------

image = Image.open(
    IMAGE_PATH
).convert("RGB")

image = image.resize(
    IMAGE_SIZE
)

image_array = np.asarray(
    image,
    dtype=np.float32
)

image_array = np.expand_dims(
    image_array,
    axis=0
)


# ------------------------------------------------------------
# TEST 1: RAW 0-255
# ------------------------------------------------------------

print("\n")
print("=" * 80)
print("TEST 1 — RAW 0-255 INPUT")
print("=" * 80)

raw_prediction = model.predict(
    image_array,
    verbose=0
)[0]

raw_index = int(
    np.argmax(raw_prediction)
)

print("\nTop predictions:")

for index in np.argsort(raw_prediction)[::-1][:5]:

    print(
        f"{CLASS_NAMES[index]:12s}: "
        f"{raw_prediction[index]:.4f}"
    )

print(
    f"\nPrediction: "
    f"{CLASS_NAMES[raw_index]}"
)


# ------------------------------------------------------------
# TEST 2: MobileNetV2 preprocess_input
# ------------------------------------------------------------

print("\n")
print("=" * 80)
print("TEST 2 — MOBILENETV2 preprocess_input")
print("=" * 80)

processed_image = (
    tf.keras.applications.mobilenet_v2.preprocess_input(
        image_array.copy()
    )
)

processed_prediction = model.predict(
    processed_image,
    verbose=0
)[0]

processed_index = int(
    np.argmax(processed_prediction)
)

print("\nTop predictions:")

for index in np.argsort(
    processed_prediction
)[::-1][:5]:

    print(
        f"{CLASS_NAMES[index]:12s}: "
        f"{processed_prediction[index]:.4f}"
    )

print(
    f"\nPrediction: "
    f"{CLASS_NAMES[processed_index]}"
)


# ------------------------------------------------------------
# Compare
# ------------------------------------------------------------

print("\n")
print("=" * 80)
print("COMPARISON")
print("=" * 80)

print(
    f"\nRaw input prediction      : "
    f"{CLASS_NAMES[raw_index]}"
)

print(
    f"Preprocessed prediction   : "
    f"{CLASS_NAMES[processed_index]}"
)

print(
    f"\nRaw confidence            : "
    f"{raw_prediction[raw_index]:.2%}"
)

print(
    f"Preprocessed confidence   : "
    f"{processed_prediction[processed_index]:.2%}"
)

print("\nTest complete.")