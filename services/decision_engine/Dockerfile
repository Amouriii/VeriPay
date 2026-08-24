FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_decision_engine/ ./veripay_decision_engine/
EXPOSE 8000
CMD ["uvicorn", "veripay_decision_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
