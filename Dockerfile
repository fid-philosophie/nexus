FROM python:3.12.16-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
    "pip>=26.2.2"

COPY pyproject.toml /app/
COPY nexus.py /app/
COPY nexus_api.py /app/

RUN python -m pip install --no-cache-dir .

RUN python -m pip check

COPY . /app/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "nexus_api:app", "--host", "0.0.0.0", "--port", "8000"]