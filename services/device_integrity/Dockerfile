FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_device_integrity/ ./veripay_device_integrity/
EXPOSE 8000
CMD ["uvicorn", "veripay_device_integrity.main:app", "--host", "0.0.0.0", "--port", "8000"]
