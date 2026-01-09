FROM python:3.12-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY flow.py .

# Variables d'environnement par défaut
ENV DRIFT_THRESHOLD=0.7
ENV CHECK_INTERVAL=30
ENV PREFECT_API_URL=http://prefect-server:4200/api

# Commande par défaut
CMD ["python", "flow.py"]
