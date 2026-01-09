FROM python:3.12.12-slim-trixie

# SHELL ["/bin/bash", "-c"]

WORKDIR /app


# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir  -r requirements.txt
RUN pip install uvicorn["standard"]

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
