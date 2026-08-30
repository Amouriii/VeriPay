# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/fi_ops_portal/Dockerfile -t veripay-fi_ops_portal .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/fi_ops_portal/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .
COPY services/fi_ops_portal/veripay_fi_ops_portal /app/veripay_fi_ops_portal/

EXPOSE 8000
CMD ["uvicorn", "veripay_fi_ops_portal.main:app", "--host", "0.0.0.0", "--port", "8000"]