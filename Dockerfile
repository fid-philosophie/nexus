FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
COPY nexus.py /app/
COPY nexus_api.py /app/

RUN pip install --upgrade pip && pip install .

COPY . /app/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "nexus_api:app", "--host", "0.0.0.0", "--port", "8000"]