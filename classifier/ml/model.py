"""
Inference wrapper around Person A's trained CNN.

Loaded once at import time (not per-request) per the Docker README, so the
~5MB checkpoint and TensorFlow graph are only paid for once per worker.

IMPORTANT / found during integration testing:
The checkpoint was saved from an older Keras version and will NOT load with
a bare `tf.keras.models.load_model(...)` on current tensorflow-cpu (2.19+,
which ships Keras 3). It fails with:

    TypeError: Could not locate function 'softmax_v2'.

This happens because the final Dense layer's activation was serialized as a
raw function reference (`tf.nn.softmax`), and Keras 3's stricter
deserialization can't resolve that name automatically. The `custom_objects`
mapping below fixes it. If Person D's Docker image pins a different
TensorFlow version, re-check whether this workaround is still needed —
newer or older TF may behave differently.
"""
import os

import numpy as np
import tensorflow as tf

MODEL_PATH = os.path.join(os.path.dirname(__file__), "mnist_cnn.keras")

_model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={"softmax_v2": tf.nn.softmax},
)
# Warm up the graph once at startup so the first real request isn't slow.
_model.predict(np.zeros((1, 28, 28, 1), dtype="float32"), verbose=0)


def preprocess_csv_array(arr):
    """
    Turn a raw 28x28 numpy array of pixel intensities into the (1,28,28,1)
    float32 tensor the model expects.

    This MUST stay identical to `preprocess_csv_array` in Person A's
    training notebook, or accuracy silently tanks in production:
    the model was trained on inputs scaled to 0-1 (x_train / 255.0), so any
    input we feed it has to be scaled the same way.

    Auto-detect rule (per the assignment spec): if the max value in the
    array is over 1.0, assume it's raw 0-255 and divide by 255. Otherwise
    assume it's already scaled 0-1 and use it as-is.
    """
    arr = np.asarray(arr, dtype="float32")
    if arr.shape != (28, 28):
        raise ValueError(f"expected 28x28, got {arr.shape}")
    if arr.max() > 1.0:
        arr = arr / 255.0
    return arr.reshape(1, 28, 28, 1)


def classify_array(arr):
    """
    Run the model on a raw 28x28 array.

    Returns (predicted_digit: int, confidence: float 0-1, probs: list[float] len 10)
    """
    x = preprocess_csv_array(arr)
    probs = _model.predict(x, verbose=0)[0]
    pred = int(np.argmax(probs))
    confidence = float(probs[pred])
    return pred, confidence, probs.tolist()
