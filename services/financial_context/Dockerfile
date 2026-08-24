FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_financial_context/ ./veripay_financial_context/
EXPOSE 8000
CMD ["uvicorn", "veripay_financial_context.main:app", "--host", "0.0.0.0", "--port", "8000"]
