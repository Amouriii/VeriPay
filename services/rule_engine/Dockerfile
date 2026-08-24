FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_rule_engine/ ./veripay_rule_engine/
EXPOSE 8000
CMD ["uvicorn", "veripay_rule_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
