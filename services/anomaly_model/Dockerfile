# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/anomaly_model/Dockerfile -t veripay-anomaly_model .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/anomaly_model/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e ".[model]"
COPY services/anomaly_model/veripay_anomaly_model /app/veripay_anomaly_model/

EXPOSE 8000
CMD ["uvicorn", "veripay_anomaly_model.main:app", "--host", "0.0.0.0", "--port", "8000"]