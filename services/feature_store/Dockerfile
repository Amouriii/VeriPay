# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/feature_store/Dockerfile -t veripay-feature_store .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/feature_store/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .
COPY services/feature_store/veripay_feature_store /app/veripay_feature_store/

EXPOSE 8000
CMD ["uvicorn", "veripay_feature_store.main:app", "--host", "0.0.0.0", "--port", "8000"]