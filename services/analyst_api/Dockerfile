# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/analyst_api/Dockerfile -t veripay-analyst_api .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/analyst_api/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .
COPY services/analyst_api/veripay_analyst_api /app/veripay_analyst_api/

EXPOSE 8000
CMD ["uvicorn", "veripay_analyst_api.main:app", "--host", "0.0.0.0", "--port", "8000"]