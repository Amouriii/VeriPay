# Build context must be the repository ROOT so the local veripay-common is available:
#   docker build -f services/feedback_loop/Dockerfile -t veripay-feedback_loop .
FROM python:3.12-slim
WORKDIR /app

# Install the shared library from source (not published to PyPI).
COPY libs/veripay_common /app/libs/veripay_common
RUN pip install --no-cache-dir /app/libs/veripay_common

# Install this service (editable so the package copied below is served).
COPY services/feedback_loop/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .
COPY services/feedback_loop/veripay_feedback_loop /app/veripay_feedback_loop/

EXPOSE 8000
CMD ["uvicorn", "veripay_feedback_loop.main:app", "--host", "0.0.0.0", "--port", "8000"]