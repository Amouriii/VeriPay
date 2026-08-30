# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/investigation_agent/Dockerfile -t veripay-investigation_agent .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/investigation_agent/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e ".[llm]"
COPY services/investigation_agent/veripay_investigation_agent /app/veripay_investigation_agent/

EXPOSE 8000
CMD ["uvicorn", "veripay_investigation_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]