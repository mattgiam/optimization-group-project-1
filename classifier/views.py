import base64
import csv
import io

import numpy as np
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .ml.model import classify_array

# Real numbers pulled from Person A's training notebook (val accuracy after
# each tuning attempt). Used to draw the progression chart on the article
# page. Keep this in sync if A retrains with a different architecture.
TUNING_LOG = [
    {
        "name": "Dense baseline",
        "detail": "Flatten \u2192 Dense(128) \u2192 Dropout \u2192 Dense(64) \u2192 Dense(10)",
        "val_accuracy": 97.71,
        "note": "No convolution yet \u2014 just a number to beat.",
    },
    {
        "name": "Add convolution",
        "detail": "Conv(32, 3\u00d73) \u2192 MaxPool \u2192 Dense(128) \u2192 Dense(10)",
        "val_accuracy": 98.55,
        "note": "One conv block already beats the dense net by almost a point.",
    },
    {
        "name": "Go deeper",
        "detail": "Two conv/pool blocks (32 then 64 filters) before flattening",
        "val_accuracy": 99.00,
        "note": "Checked the flatten size (7\u00d77\u00d764 = 3,136) to confirm we hadn't over-pooled.",
    },
    {
        "name": "Fight overfitting",
        "detail": "Same shape, with dropout after each block and before the output layer",
        "val_accuracy": 99.23,
        "note": "Training accuracy had started running ahead of validation \u2014 dropout closed the gap.",
    },
    {
        "name": "BatchNorm + double conv",
        "detail": "Two conv+BatchNorm layers per block, smaller batch size (128)",
        "val_accuracy": 99.39,
        "note": "The winner. Epoch 1's validation accuracy briefly cratered to ~28% before batch norm settled in.",
    },
]

MIXUPS = [
    {"true": 4, "pred": 9, "count": 6},
    {"true": 9, "pred": 4, "count": 5},
    {"true": 5, "pred": 3, "count": 4},
    {"true": 7, "pred": 2, "count": 3},
    {"true": 7, "pred": 1, "count": 3},
    {"true": 3, "pred": 5, "count": 3},
    {"true": 9, "pred": 7, "count": 2},
    {"true": 9, "pred": 5, "count": 2},
]


@login_required
def article(request):
    context = {
        "tuning_log": TUNING_LOG,
        "best_val_accuracy": max(row["val_accuracy"] for row in TUNING_LOG),
        "test_accuracy": 99.5,
        "test_wrong": 50,
        "test_total": 10000,
        "mixups": MIXUPS,
    }
    return render(request, "classifier/article.html", context)


def _read_csv_grid(uploaded_file):
    """
    Parse an uploaded file into a list-of-lists of raw string cells.
    Raises ValueError with a user-facing message on any structural problem.
    Does not check numeric validity yet -- see _validate_and_build_array.
    """
    if not uploaded_file.name.lower().endswith(".csv"):
        raise ValueError("That file doesn't look like a CSV. Please upload a .csv file.")

    if uploaded_file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValueError("That file is too large to be a 28\u00d728 pixel grid. Please upload a smaller CSV.")

    try:
        raw = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("That file doesn't look like a CSV. Please upload a .csv file.")

    rows = [row for row in csv.reader(io.StringIO(raw)) if row]

    if not rows:
        raise ValueError("That CSV file is empty.")

    return rows


def _validate_and_build_array(rows):
    """
    Take parsed CSV rows and return a validated (28, 28) float64 numpy array,
    or raise ValueError with the exact message the page should show.
    """
    if len(rows) != 28:
        raise ValueError(f"CSV must have exactly 28 rows, found {len(rows)}.")

    bad_row = next((r for r in rows if len(r) != 28), None)
    if bad_row is not None:
        raise ValueError(f"CSV must have exactly 28 columns, found a row with {len(bad_row)}.")

    try:
        arr = np.array(rows, dtype="float64")
    except ValueError:
        raise ValueError("CSV contains non-numeric values.")

    if np.isnan(arr).any():
        raise ValueError("CSV contains non-numeric values.")

    if arr.min() < 0:
        raise ValueError(f"Pixel values can't be negative. Found a value of {arr.min():g}.")

    if arr.max() > 255:
        raise ValueError(f"Pixel values must be 0\u2013255 (or 0\u20131 if pre-scaled). Found a value of {arr.max():g}.")

    return arr


def _array_to_data_uri(arr):
    """Render the (28,28) array back as a small inline PNG the browser can show."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    display_arr = arr / 255.0 if arr.max() > 1.0 else arr

    fig = plt.figure(figsize=(3, 3), dpi=110)
    plt.pcolormesh(1 - display_arr[::-1, :], cmap="gray", vmin=0, vmax=1)
    plt.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@login_required
def classify(request):
    context = {}

    if request.method == "POST":
        # A fresh upload attempt supersedes whatever was classified before,
        # whether this attempt succeeds or fails.
        request.session.pop("classify_result", None)

        uploaded_file = request.FILES.get("csv_file")
        try:
            if uploaded_file is None:
                raise ValueError("Please choose a CSV file to upload.")
            rows = _read_csv_grid(uploaded_file)
            arr = _validate_and_build_array(rows)
        except ValueError as exc:
            # Validation errors are shown immediately, no redirect -- the
            # person is almost certainly about to try another file.
            context["error"] = str(exc)
            return render(request, "classifier/classify.html", context)

        pred, confidence, probs = classify_array(arr)
        pct = [round(p * 100, 1) for p in probs]
        # Success goes through POST/redirect/GET and the result lives in the
        # session, so refreshing the results page doesn't re-submit the
        # upload, and "Start over" has session state to actually clear.
        request.session["classify_result"] = {
            "digit": pred,
            "confidence": round(confidence * 100, 1),
            "pct": pct,
            "image_data_uri": _array_to_data_uri(arr),
            "was_rescaled": bool(arr.max() > 1.0),
        }
        return redirect("classify")

    stored = request.session.get("classify_result")
    if stored:
        context["result"] = {
            "digit": stored["digit"],
            "confidence": stored["confidence"],
            "rows": [{"digit": d, "pct": stored["pct"][d]} for d in range(10)],
            "image_data_uri": stored["image_data_uri"],
            "was_rescaled": stored["was_rescaled"],
        }

    return render(request, "classifier/classify.html", context)


@login_required
def reset_classifier(request):
    request.session.pop("classify_result", None)
    return redirect("classify")
