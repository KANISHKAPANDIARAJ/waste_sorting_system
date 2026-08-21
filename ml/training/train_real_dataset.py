import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import pickle
import cv2
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

from ml.preprocessing import preprocess_image, extract_features


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_DIR = r"D:\archive\standardized_256"

MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models")
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "waste_classifier.pkl"
)

IMAGE_SIZE = (64, 64)

RANDOM_STATE = 42


# ============================================================
# DATASET CLASS MAPPING
# ============================================================
#
# Dataset classes:
#
# battery
# biological
# cardboard
# clothes
# glass
# metal
# paper
# plastic
# shoes
# trash
#
# Existing application classes:
#
# Plastic
# Paper
# Metal
# Organic
# Other
#
# ============================================================

CLASS_MAPPING = {
    "battery": "Other",
    "biological": "Organic",
    "cardboard": "Paper",
    "clothes": "Other",
    "glass": "Other",
    "metal": "Metal",
    "paper": "Paper",
    "plastic": "Plastic",
    "shoes": "Other",
    "trash": "Other",
}


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    X = []
    y = []

    original_counts = {}
    mapped_counts = {}

    class_directories = [
        d for d in os.listdir(DATASET_DIR)
        if os.path.isdir(os.path.join(DATASET_DIR, d))
    ]

    print("\nDataset classes found:")

    for original_class in sorted(class_directories):

        if original_class not in CLASS_MAPPING:
            print(f"Skipping unknown class: {original_class}")
            continue

        mapped_class = CLASS_MAPPING[original_class]

        class_dir = os.path.join(
            DATASET_DIR,
            original_class
        )

        files = [
            f for f in os.listdir(class_dir)
            if f.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            )
        ]

        original_counts[original_class] = len(files)

        mapped_counts[mapped_class] = (
            mapped_counts.get(mapped_class, 0) + len(files)
        )

        print(
            f"{original_class:12s} -> "
            f"{mapped_class:8s} : "
            f"{len(files)} images"
        )

        for filename in files:

            image_path = os.path.join(
                class_dir,
                filename
            )

            try:

                gray_img, color_img = preprocess_image(
                    image_path,
                    target_size=IMAGE_SIZE
                )

                features = extract_features(
                    color_img,
                    gray_img
                )

                X.append(features)
                y.append(mapped_class)

            except Exception as e:

                print(
                    f"Skipping {image_path}: {e}"
                )

    print("\nMapped class totals:")

    for class_name, count in sorted(mapped_counts.items()):
        print(
            f"{class_name:10s}: {count}"
        )

    return np.array(X), np.array(y)


# ============================================================
# TRAIN
# ============================================================

def train():

    print("=" * 70)
    print("REAL WASTE DATASET TRAINING")
    print("=" * 70)

    print(f"\nDataset:")
    print(DATASET_DIR)

    print(f"\nModel output:")
    print(MODEL_PATH)

    X, y = load_dataset()

    print("\nFeature matrix shape:")
    print(X.shape)

    print("\nTotal samples:")
    print(len(X))

    print("\nClasses:")
    print(sorted(set(y)))

    # --------------------------------------------------------
    # Train / validation split
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print("\nTraining samples:", len(X_train))
    print("Testing samples :", len(X_test))

    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    print("\nTraining Random Forest...")

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced"
    )

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print("\n" + "=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)

    print(
        f"\nValidation Accuracy: "
        f"{accuracy * 100:.2f}%"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("\nConfusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            predictions
        )
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    with open(
        MODEL_PATH,
        "wb"
    ) as f:

        pickle.dump(
            model,
            f
        )

    print("\n" + "=" * 70)
    print("MODEL SAVED")
    print("=" * 70)

    print(
        f"\n{MODEL_PATH}"
    )

    print(
        "\nClasses stored in model:"
    )

    print(
        model.classes_
    )


if __name__ == "__main__":
    train()