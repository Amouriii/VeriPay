FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_business_portal/ ./veripay_business_portal/
EXPOSE 8000
CMD ["uvicorn", "veripay_business_portal.main:app", "--host", "0.0.0.0", "--port", "8000"]
