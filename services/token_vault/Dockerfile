# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/token_vault/Dockerfile -t veripay-token_vault .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/token_vault/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .
COPY services/token_vault/veripay_token_vault /app/veripay_token_vault/

EXPOSE 8000
CMD ["uvicorn", "veripay_token_vault.main:app", "--host", "0.0.0.0", "--port", "8000"]