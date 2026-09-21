
FROM python:3.13-slim



WORKDIR /app



COPY requirements.txt .



RUN pip install --no-cache-dir --upgrade pip \

    && pip install --no-cache-dir -r requirements.txt



COPY . .



RUN DJANGO_SECRET_KEY=build-only-key python manage.py collectstatic --noinput



EXPOSE 8000



CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
