FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_merchant_policy/ ./veripay_merchant_policy/
EXPOSE 8000
CMD ["uvicorn", "veripay_merchant_policy.main:app", "--host", "0.0.0.0", "--port", "8000"]
