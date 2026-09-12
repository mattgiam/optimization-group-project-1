"""ml/model.py — load the model once at import; preprocess and classify."""

import os

import numpy as np
import tensorflow as tf

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'mnist_cnn.keras')

print(f'Loading model from {MODEL_PATH} ...')
model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={'softmax_v2': tf.nn.softmax},
)
print('Model loaded successfully.')


def preprocess_csv_array(arr):
    """Validate a 28x28 array, auto-detect 0-255 vs 0-1, reshape for the model."""
    arr = np.asarray(arr, dtype='float32')

    if arr.shape != (28, 28):
        raise ValueError(f'expected 28x28, got {arr.shape}')
    if np.isnan(arr).any():
        raise ValueError('array contains NaN values')
    if arr.min() < 0:
        raise ValueError('array contains negative values')

    if arr.max() > 1.0:
        if arr.max() > 255:
            raise ValueError(f'pixel values exceed 255 (found {arr.max()})')
        arr = arr / 255.0

    return arr.reshape(1, 28, 28, 1)


def classify_image(arr):
    """Run inference. Returns predicted digit, confidence, and all probabilities."""
    pred_probs = model.predict(arr, verbose=0)[0]
    predicted_digit = int(np.argmax(pred_probs))

    return {
        'predicted_digit': predicted_digit,
        'confidence': float(pred_probs[predicted_digit]),
        'probabilities': {int(i): float(pred_probs[i]) for i in range(10)},
    }
