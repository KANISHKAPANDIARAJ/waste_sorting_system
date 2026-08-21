import os
from pathlib import Path
from collections import Counter

DATASET_DIR = Path(r"D:\archive\standardized_256")

EXPECTED_CLASSES = [
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

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

print("=" * 70)
print("WASTE DATASET DIAGNOSTIC")
print("=" * 70)

if not DATASET_DIR.exists():
    print("\n❌ Dataset directory does not exist:")
    print(DATASET_DIR)
    print("\nChange DATASET_DIR to the actual location of standardized_256.")
    raise SystemExit

print(f"\nDataset: {DATASET_DIR}\n")

# --------------------------------------------------
# 1. Check folders
# --------------------------------------------------

folders = [x for x in DATASET_DIR.iterdir() if x.is_dir()]

print("FOLDERS FOUND")
print("-" * 70)

for folder in sorted(folders):
    print(folder.name)

# --------------------------------------------------
# 2. Count images
# --------------------------------------------------

print("\n\nIMAGE COUNT PER CLASS")
print("-" * 70)

total = 0
counts = {}

for class_name in EXPECTED_CLASSES:

    class_dir = DATASET_DIR / class_name

    if not class_dir.exists():
        print(f"{class_name:<15} ❌ MISSING")
        counts[class_name] = 0
        continue

    images = [
        f for f in class_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    counts[class_name] = len(images)
    total += len(images)

    print(f"{class_name:<15} {len(images):>6}")

print("-" * 70)
print(f"{'TOTAL':<15} {total:>6}")

# --------------------------------------------------
# 3. Compare class balance
# --------------------------------------------------

print("\n\nCLASS BALANCE")
print("-" * 70)

nonzero = [x for x in counts.values() if x > 0]

if nonzero:

    maximum = max(nonzero)
    minimum = min(nonzero)

    print(f"Maximum class size : {maximum}")
    print(f"Minimum class size : {minimum}")
    print(f"Max/Min ratio      : {maximum / minimum:.2f}x")

    print("\nRelative distribution:")

    for class_name in EXPECTED_CLASSES:

        count = counts[class_name]

        if count:
            percentage = (count / total) * 100
            print(
                f"{class_name:<15} "
                f"{count:>6} "
                f"({percentage:>5.2f}%)"
            )

# --------------------------------------------------
# 4. Look for nested folders
# --------------------------------------------------

print("\n\nNESTED FOLDER CHECK")
print("-" * 70)

nested_found = False

for class_name in EXPECTED_CLASSES:

    class_dir = DATASET_DIR / class_name

    if not class_dir.exists():
        continue

    subfolders = [x for x in class_dir.iterdir() if x.is_dir()]

    if subfolders:

        nested_found = True

        print(f"\n⚠️ {class_name} contains subfolders:")

        for subfolder in subfolders:
            print(f"   └── {subfolder.name}")

if not nested_found:
    print("✅ No unexpected nested folders found.")

# --------------------------------------------------
# 5. Check files directly inside class folders
# --------------------------------------------------

print("\n\nDIRECT IMAGE CHECK")
print("-" * 70)

for class_name in EXPECTED_CLASSES:

    class_dir = DATASET_DIR / class_name

    if not class_dir.exists():
        continue

    direct_images = [
        f for f in class_dir.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    print(f"{class_name:<15} {len(direct_images):>6} direct images")

# --------------------------------------------------
# 6. Final assessment
# --------------------------------------------------

print("\n\nFINAL ASSESSMENT")
print("=" * 70)

missing = [
    name for name in EXPECTED_CLASSES
    if counts[name] == 0
]

if missing:
    print("\n❌ Missing classes:")
    for name in missing:
        print("   -", name)

else:
    print("\n✅ All 10 expected classes exist.")

if nonzero:

    ratio = max(nonzero) / min(nonzero)

    if ratio > 3:
        print(
            "\n⚠️ Significant class imbalance detected."
        )
    else:
        print(
            "\n✅ No extreme class imbalance detected."
        )

print("\nDiagnostic complete.")