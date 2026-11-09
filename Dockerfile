FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances d'abord : cette couche est réutilisée tant que requirements.txt ne change pas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Version affichée sur /version
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION

# Utilisateur non-root
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]