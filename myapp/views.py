"""myapp/views.py — login, article page, upload, classification, results."""

import base64
import io

import matplotlib
matplotlib.use('Agg')          # MUST come before pyplot is imported
import matplotlib.pyplot as plt

import numpy as np
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ml.model import classify_image, preprocess_csv_array

from .forms import CSVUploadForm


class CustomLoginView(LoginView):
    template_name = 'myapp/login.html'
    redirect_authenticated_user = True


@login_required(login_url='login')
def about_view(request):
    """Article page describing the network. Person C fills in the content."""
    return render(request, 'myapp/about.html')


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def upload_view(request):
    form = CSVUploadForm()
    error = None

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            request.session['last_image_array'] = form.validated_array.tolist()
            return redirect('results')
        error = list(form.errors.values())[0][0] if form.errors else 'Unknown error'

    return render(request, 'myapp/upload.html', {'form': form, 'error': error})


@login_required(login_url='login')
@require_http_methods(['GET'])
def results_view(request):
    image_list = request.session.get('last_image_array')
    if image_list is None:
        return redirect('upload')

    arr = np.array(image_list, dtype='float32')

    try:
        result = classify_image(preprocess_csv_array(arr))
    except Exception as exc:
        return render(request, 'myapp/results.html',
                      {'error': f'Classification error: {exc}'})

    bars = [
        (digit, round(prob * 100, 1), f'{prob * 100:.1f}%')
        for digit, prob in sorted(result['probabilities'].items())
    ]

    context = {
        'predicted_digit': result['predicted_digit'],
        'confidence': f"{result['confidence'] * 100:.2f}%",
        'bars': bars,
        'image_base64': array_to_base64_png(arr),
    }

    request.session.pop('last_image_array', None)
    return render(request, 'myapp/results.html', context)


@login_required(login_url='login')
@require_http_methods(['GET'])
def start_over_view(request):
    request.session.pop('last_image_array', None)
    return redirect('upload')


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')


def array_to_base64_png(arr):
    """Render a 28x28 array as an inline PNG data URI."""
    if arr.max() > 1.0:
        arr = arr / 255.0

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(1 - arr, cmap='gray', vmin=0, vmax=1)
    ax.axis('off')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=60)
    plt.close(fig)
    buffer.seek(0)

    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{encoded}'
