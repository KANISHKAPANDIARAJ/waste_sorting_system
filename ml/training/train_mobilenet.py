import os
import sys
import json
import numpy as np
import tensorflow as tf

from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_DIR = r"D:\archive\standardized_256"

MODEL_DIR = os.path.join(
    PROJECT_ROOT,
    "ml",
    "models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "waste_mobilenetv2.keras"
)

CLASS_NAMES_PATH = os.path.join(
    MODEL_DIR,
    "waste_class_names.json"
)

IMAGE_SIZE = (224, 224)

BATCH_SIZE = 32

EPOCHS = 15

SEED = 42


# ============================================================
# ORIGINAL DATASET CLASSES
# ============================================================

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
    "trash",
]


# ============================================================
# VERIFY DATASET
# ============================================================

print("=" * 70)
print("MOBILENETV2 WASTE CLASSIFIER TRAINING")
print("=" * 70)

print("\nDataset:")
print(DATASET_DIR)

print("\nModel:")
print(MODEL_PATH)

print("\nChecking dataset...")

for class_name in CLASS_NAMES:

    class_dir = os.path.join(
        DATASET_DIR,
        class_name
    )

    if not os.path.isdir(class_dir):

        raise FileNotFoundError(
            f"Missing dataset class: {class_dir}"
        )

    count = len([
        f
        for f in os.listdir(class_dir)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        )
    ])

    print(
        f"{class_name:12s}: {count} images"
    )


# ============================================================
# LOAD TRAINING DATA
# ============================================================

print("\nLoading dataset...")

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    labels="inferred",
    label_mode="int",
    class_names=CLASS_NAMES,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    validation_split=0.20,
    subset="training",
    seed=SEED,
    shuffle=True,
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    labels="inferred",
    label_mode="int",
    class_names=CLASS_NAMES,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    validation_split=0.20,
    subset="validation",
    seed=SEED,
    shuffle=False,
)


print("\nClass names used by TensorFlow:")

print(CLASS_NAMES)


# ============================================================
# PERFORMANCE PIPELINE
# ============================================================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.prefetch(
    AUTOTUNE
)

val_ds = val_ds.prefetch(
    AUTOTUNE
)


# ============================================================
# DATA AUGMENTATION
# ============================================================

data_augmentation = tf.keras.Sequential(
    [
        layers.RandomFlip(
            "horizontal"
        ),

        layers.RandomRotation(
            0.08
        ),

        layers.RandomZoom(
            0.10
        ),

        layers.RandomContrast(
            0.10
        ),
    ],
    name="data_augmentation"
)


# ============================================================
# MOBILE NET V2 BASE
# ============================================================

print("\nLoading MobileNetV2...")

base_model = MobileNetV2(
    input_shape=(
        IMAGE_SIZE[0],
        IMAGE_SIZE[1],
        3
    ),

    include_top=False,

    weights="imagenet"
)


# Freeze pretrained layers initially

base_model.trainable = False


# ============================================================
# BUILD MODEL
# ============================================================

inputs = layers.Input(
    shape=(
        IMAGE_SIZE[0],
        IMAGE_SIZE[1],
        3
    )
)

x = data_augmentation(
    inputs
)

x = tf.keras.applications.mobilenet_v2.preprocess_input(
    x
)

x = base_model(
    x,
    training=False
)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dropout(
    0.30
)(x)

outputs = layers.Dense(
    len(CLASS_NAMES),
    activation="softmax"
)(x)


model = models.Model(
    inputs,
    outputs
)


# ============================================================
# COMPILE
# ============================================================

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ]
)


model.summary()


# ============================================================
# CALLBACKS
# ============================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)

callbacks = [

    ModelCheckpoint(
        MODEL_PATH,
        monitor="val_accuracy",
        save_best_only=True,
        verbose=1
    ),

    EarlyStopping(
        monitor="val_accuracy",
        patience=4,
        restore_best_weights=True,
        verbose=1
    ),

    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.3,
        patience=2,
        min_lr=1e-6,
        verbose=1
    )
]


# ============================================================
# TRAIN CLASSIFICATION HEAD
# ============================================================

print("\n")
print("=" * 70)
print("PHASE 1: TRAINING CLASSIFICATION HEAD")
print("=" * 70)

history = model.fit(
    train_ds,

    validation_data=val_ds,

    epochs=EPOCHS,

    callbacks=callbacks
)


# ============================================================
# FINE TUNING
# ============================================================

print("\n")
print("=" * 70)
print("PHASE 2: FINE-TUNING MOBILE NET V2")
print("=" * 70)


base_model.trainable = True


# Freeze most layers.
# Only the final part of MobileNetV2 is fine-tuned.

fine_tune_from = 100

for layer in base_model.layers[
    :fine_tune_from
]:

    layer.trainable = False


model.compile(

    optimizer=tf.keras.optimizers.Adam(
        learning_rate=1e-5
    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ]
)


fine_tune_callbacks = [

    ModelCheckpoint(
        MODEL_PATH,
        monitor="val_accuracy",
        save_best_only=True,
        verbose=1
    ),

    EarlyStopping(
        monitor="val_accuracy",
        patience=3,
        restore_best_weights=True,
        verbose=1
    ),

    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.3,
        patience=2,
        min_lr=1e-7,
        verbose=1
    )
]


model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=8,

    callbacks=fine_tune_callbacks
)


# ============================================================
# FINAL EVALUATION
# ============================================================

print("\n")
print("=" * 70)
print("FINAL MODEL EVALUATION")
print("=" * 70)

loss, accuracy = model.evaluate(
    val_ds,
    verbose=1
)

print(
    f"\nValidation Accuracy: "
    f"{accuracy * 100:.2f}%"
)

print(
    f"Validation Loss: "
    f"{loss:.4f}"
)


# ============================================================
# SAVE MODEL
# ============================================================

model.save(
    MODEL_PATH
)


with open(
    CLASS_NAMES_PATH,
    "w"
) as f:

    json.dump(
        CLASS_NAMES,
        f,
        indent=4
    )


print("\n")
print("=" * 70)
print("MODEL SAVED")
print("=" * 70)

print(
    "\nModel:"
)

print(
    MODEL_PATH
)

print(
    "\nClasses:"
)

print(
    CLASS_NAMES_PATH
)

print("\nTraining completed successfully.")