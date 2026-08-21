from pathlib import Path
import random

from ml.classifier import WasteClassifier


DATASET_DIR = Path(r"D:\archive\standardized_256")

CLASSES = [
    "battery",
    "biological",
    "cardboard",
    "clothes",
    "glass",
    "metal",
    "paper",
    "plastic",
    "shoes",
    "trash",
]


classifier = WasteClassifier()

print("=" * 80)
print("REAL DATASET IMAGE TEST — CORRECT INFERENCE PIPELINE")
print("=" * 80)

correct = 0
total = 0

for class_name in CLASSES:

    folder = DATASET_DIR / class_name

    images = [
        p
        for p in folder.iterdir()
        if p.is_file()
        and p.suffix.lower() in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }
    ]

    image = random.choice(images)

    result = classifier.predict(str(image))

    predicted = result["raw_class"]
    confidence = result["confidence"]

    is_correct = predicted == class_name

    if is_correct:
        correct += 1

    total += 1

    status = "✅" if is_correct else "❌"

    print()
    print(f"{status} ACTUAL: {class_name}")
    print(f"Image      : {image.name}")
    print(f"Prediction : {predicted}")
    print(f"Confidence : {confidence:.2%}")

print()
print("=" * 80)
print("RESULT")
print("=" * 80)

print(
    f"\nRandom-image accuracy: "
    f"{correct}/{total} = {correct / total:.2%}"
)

print("\nTest complete.")