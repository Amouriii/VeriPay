FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_auth_orchestration/ ./veripay_auth_orchestration/
EXPOSE 8000
CMD ["uvicorn", "veripay_auth_orchestration.main:app", "--host", "0.0.0.0", "--port", "8000"]
