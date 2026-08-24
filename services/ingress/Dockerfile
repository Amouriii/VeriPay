FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_ingress/ ./veripay_ingress/
EXPOSE 8000
CMD ["uvicorn", "veripay_ingress.main:app", "--host", "0.0.0.0", "--port", "8000"]
