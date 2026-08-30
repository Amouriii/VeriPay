# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/merchant_ingress/Dockerfile -t veripay-merchant_ingress .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/merchant_ingress/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .
COPY services/merchant_ingress/veripay_merchant_ingress /app/veripay_merchant_ingress/

EXPOSE 8000
CMD ["uvicorn", "veripay_merchant_ingress.main:app", "--host", "0.0.0.0", "--port", "8000"]