# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/banking_gateway/Dockerfile -t veripay-banking_gateway .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/banking_gateway/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .
COPY services/banking_gateway/veripay_banking_gateway /app/veripay_banking_gateway/

EXPOSE 8000
CMD ["uvicorn", "veripay_banking_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]