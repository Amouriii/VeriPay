FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_token_vault/ ./veripay_token_vault/
EXPOSE 8000
CMD ["uvicorn", "veripay_token_vault.main:app", "--host", "0.0.0.0", "--port", "8000"]
