FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_anomaly_model/ ./veripay_anomaly_model/
EXPOSE 8000
CMD ["uvicorn", "veripay_anomaly_model.main:app", "--host", "0.0.0.0", "--port", "8000"]
