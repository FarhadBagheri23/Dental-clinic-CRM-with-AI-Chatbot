# Data service: generates the clinic CSVs and loads them into MongoDB.
# One image, two entrypoints — `seed.py` (default) and `generate_data.py`,
# run via the `generate` compose profile.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY seeder/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY seeder/seed.py .
COPY scripts/generate_data.py ./scripts/generate_data.py

# Run as a non-root user; it only needs to write to the mounted /data volume.
RUN useradd --create-home --uid 10001 seeder && chown -R seeder /app
USER seeder

CMD ["python", "seed.py"]
