"""myapp/forms.py — CSV upload form and validation."""

import csv
import io

import numpy as np
from django import forms


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='Upload 28x28 CSV file',
        help_text='Exactly 28 rows x 28 columns, no header. Values 0-255 or 0-1.',
        widget=forms.FileInput(attrs={'accept': '.csv'}),
    )

    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if not file:
            raise forms.ValidationError('No file uploaded.')
        if not file.name.lower().endswith('.csv'):
            raise forms.ValidationError('File must be a .csv file.')

        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            raise forms.ValidationError('File must be a valid text CSV.')

        rows = [r for r in csv.reader(io.StringIO(content)) if r]

        if len(rows) != 28:
            raise forms.ValidationError(
                f'CSV must have exactly 28 rows, found {len(rows)}.')

        for i, row in enumerate(rows):
            if len(row) != 28:
                raise forms.ValidationError(
                    f'Row {i + 1} has {len(row)} columns, expected 28.')

        try:
            arr = np.array([[float(v) for v in row] for row in rows],
                           dtype='float32')
        except ValueError:
            raise forms.ValidationError('CSV contains non-numeric values.')

        if np.isnan(arr).any():
            raise forms.ValidationError('CSV contains NaN values.')
        if arr.min() < 0:
            raise forms.ValidationError('CSV contains negative values.')
        if arr.max() > 255:
            raise forms.ValidationError(
                f'Pixel values exceed 255 (found {arr.max():.1f}).')

        self.validated_array = arr
        return file
