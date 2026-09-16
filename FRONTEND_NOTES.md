# MNIST Classifier — frontend build (Task C)

This is a complete, working Django site for Group Project 1: login, the
article page, and the CSV-upload classifier, styled per the "site
appearance is 50% of the grade" note. It runs end-to-end right now,
including real inference from `mnist_cnn.keras`.

## Quickstart

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate      # also seeds the dan / Optimization1234 account
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`, log in as `dan` / `Optimization1234`.
There is no signup page anywhere in the project, by design.

## What's in here

```
classifier/
  ml/
    mnist_cnn.keras     <- Person A's trained model
    model.py            <- loads it once at import time, runs inference
  templates/
    base.html            <- shared nav/footer, loads fonts + CSS
    registration/login.html
    classifier/article.html
    classifier/classify.html
  static/classifier/
    css/style.css        <- the whole design system
    images/               <- misclassified.png, confusion_matrix.png (pulled from A's notebook)
  views.py               <- article view + upload/validate/classify view
  urls.py
  migrations/0002_seed_dan.py   <- creates the dan account on `migrate`
```

## Found while wiring this up: a real model-loading bug

`mnist_cnn.keras` does **not** load with a plain
`tf.keras.models.load_model(...)` on current TensorFlow (2.19+, Keras 3).
It throws:

```
TypeError: Could not locate function 'softmax_v2'.
```

The checkpoint stores the output layer's activation as a raw function
reference, which older Keras serialized differently than Keras 3
deserializes it. The fix (already in `classifier/ml/model.py`):

```python
tf.keras.models.load_model(MODEL_PATH, custom_objects={"softmax_v2": tf.nn.softmax})
```

**Person D should know about this before building the Docker image.**
If the Dockerfile's `tensorflow-cpu` version resolves differently than
what's pinned in `requirements.txt` here, re-test that this workaround is
still needed — it's the kind of thing that works fine locally and then
silently 500s in a container. Confirmed working with `tensorflow-cpu==2.21.0`.

I verified the fixed loader against the provided `sample_data.csv`: it
predicts **8 at 100% confidence**, matching what both of you reported.

## Design system

Two typefaces, each with one job: **Source Serif 4** for the article
(the written record), **IBM Plex Mono** for everything else — nav, forms,
buttons, and every number on the site (nav/buttons/data are the
"instrument," which is why they're set differently than the prose).
One accent color (blueprint blue) carries all interactive/positive
meaning; brick red is reserved only for validation errors so it stays
meaningful. The login page's watermark is an actual pixel-grid rendering
of `sample_data.csv` — literally your test file, turned into the one
bold visual moment on the site.

All of this lives in `static/classifier/css/style.css` as CSS custom
properties (`:root { --ink, --paper, --blueprint, ... }`) if you want to
retheme anything.

Fonts load from Google Fonts via CDN (see `base.html`). That needs
outbound internet from wherever this is hosted — true on Lightsail, but
worth knowing if you ever run it somewhere locked down. Falls back to
system serif/mono if the request fails, so it degrades gracefully.

## If you're reconciling this with Saad's existing version

This was built without access to Saad's actual `views.py`/templates, so
if you want to merge rather than replace, here's the contract this
frontend expects:

**URL names:** `login`, `logout`, `article`, `classify`, `classify_reset`

**Article view context:** `tuning_log` (list of dicts with `name`,
`detail`, `val_accuracy`, `note`), `best_val_accuracy`, `test_accuracy`,
`test_wrong`, `test_total`, `mixups` (list of dicts with `true`, `pred`,
`count`). All in `views.py` as plain Python constants — replace with
Person A's real logged data if it differs from what's checked in.

**Classify view context:** on error, `error` (string). On success,
`result` — a dict with `digit`, `confidence` (0–100 float), `rows`
(list of 10 dicts: `{"digit": d, "pct": p}`, needed because Django
templates can't index a list by a loop variable), `image_data_uri`
(a full `data:image/png;base64,...` string), `was_rescaled` (bool).

Honestly, the simplest path is probably to just use this version's
`views.py` wholesale — it already implements every validation rule from
the spec with the exact error strings Saad tested against (27-row file,
non-numeric, wrong extension, out-of-range), plus the auto-scaling
detection. Diff it against Saad's if you want to double check nothing's
missing.

## Known gap

The article has a placeholder block where the "matched set of
well-classified, high-confidence digits" should go (the assignment asks
for this alongside the misclassified grid — it's Person A's export, not
something to fabricate on the frontend side). Drop the exported PNG into
`static/classifier/images/` and swap the placeholder `<div>` in
`article.html` for an `<img>` once it exists.

## Screenshots

Login, article, and classify (empty / result / error states) were all
tested against a live local server — see the conversation for the actual
renders. Everything above was verified working, not just written.
