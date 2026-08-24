FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_corporate_spend/ ./veripay_corporate_spend/
EXPOSE 8000
CMD ["uvicorn", "veripay_corporate_spend.main:app", "--host", "0.0.0.0", "--port", "8000"]
