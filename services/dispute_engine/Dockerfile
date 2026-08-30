# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/dispute_engine/Dockerfile -t veripay-dispute_engine .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/dispute_engine/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .
COPY services/dispute_engine/veripay_dispute_engine /app/veripay_dispute_engine/

EXPOSE 8000
CMD ["uvicorn", "veripay_dispute_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]