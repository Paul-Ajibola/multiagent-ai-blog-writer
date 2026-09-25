FROM python:3.11-slim

WORKDIR /app

# psycopg needs libpq at build time if not using psycopg[binary]
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Directories at runtime
RUN mkdir -p templates static images outputs

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
