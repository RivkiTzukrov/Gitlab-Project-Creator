FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y build-essential \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
