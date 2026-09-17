# Task B Handoff — Django Backend

Backend is working end to end: login, CSV upload, validation, model inference, results display. All tested locally.

## Routes

| URL | Name | Notes |
|---|---|---|
| `/login/` | `login` | Only page not behind auth |
| `/about/` | `about` | Article page — Aryan owns the content |
| `/upload/` | `upload` | Classifier page |
| `/results/` | `results` | After a successful upload |
| `/start-over/` | `start_over` | Clears session, back to upload |
| `/logout/` | `logout` | |

Instructor account is `dan` / `Optimization1234`. No signup route — accounts come from `createsuperuser` only.

## Version constraints (read before installing anything)

David trained on TensorFlow 2.20 / Keras 3.13.2. Two gotchas:

**1. Python 3.9 cannot load the model.** On 3.9 the newest Keras available is 3.10, which doesn't understand the `quantization_config` field in David's save format. You get a wall of `TypeError: could not be deserialized properly`. Use Python 3.12 or 3.13.

**2. The model needs a `custom_objects` argument.** David's output layer used `activation=tf.nn.softmax` rather than `activation='softmax'`, so Keras serialized it as `softmax_v2` and can't resolve that name on load. `ml/model.py` handles it:

```python
model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={'softmax_v2': tf.nn.softmax},
)
```

Don't remove that argument.

## Template context variables (for Aryan)

Restyle the templates freely — just keep these names and the `{% url %}` tags.

**login.html** — `form` (Django auth form: `form.username`, `form.password`, `form.errors`)

**upload.html**
- `form` — `form.csv_file`, `form.csv_file.label`, `form.csv_file.help_text`
- `error` — validation error string, empty otherwise. Style this.

**results.html**
- `predicted_digit` — int 0–9
- `confidence` — pre-formatted string, e.g. `"100.00%"`
- `bars` — list of 10 tuples `(digit, percent, label)`. Loop with `{% for digit, pct, label in bars %}`. There's a `<div class="bar" style="width: {{ pct }}%">` hook with no CSS on it yet — confidence bars would look good there.
- `image_base64` — `data:image/png;base64,...` URI, drop into `<img src="...">`
- `error` — set instead of the above if classification fails

**about.html** — nothing passed; it's all yours.

Static files go in `static/`. `STATIC_URL` is configured.

## Article content (from David's notebook)

- Tuning: dense only 97.71% → 1 conv 98.55% → 2 conv 99.00% → + dropout 99.23% → + batch norm **99.39%** (winner)
- Final test accuracy: **99.50%**, 50 wrong out of 10,000
- Common mix-ups: 4→9 (6), 9→4 (5), 5→3 (4), 7→2 (3), 7→1 (3)
- On 100%: not achievable — some MNIST test labels are genuinely ambiguous or mislabeled, which caps accuracy below 100%
- Figures: ask David for `misclassified.png` and `confusion_matrix.png`

## Docker notes (for Matthew)

- Base image: **`python:3.13-slim`**
- **Change `tensorflow` to `tensorflow-cpu` in requirements.txt.** Mine says `tensorflow` because `tensorflow-cpu` has no macOS build; the container runs Linux where it exists and is much smaller.
- Map container port 8000 → host port 8000
- `ml/mnist_cnn.keras` (5.5 MB) is committed, so it ships with the build
- Model loads at import, so first container start takes a few seconds
- Run `migrate` and `createsuperuser` inside the container — `db.sqlite3` is gitignored, so the `dan` account doesn't travel with the repo
- Set `DEBUG = False` in `myproject/settings.py` before going live

Local run:

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

## Testing done

| Case | Result |
|---|---|
| Valid 0–1 CSV (`sample_data.csv`) | Classifies as 8, 100% confidence |
| Valid 0–255 CSV | Classifies as 8 — auto-detect works |
| 27-row CSV | "CSV must have exactly 28 rows, found 27" |
| Non-numeric values | "CSV contains non-numeric values" |
| Non-CSV file | Rejected |
| Login with `dan` | Works |
| Start-over button | Clears session, returns to upload |
