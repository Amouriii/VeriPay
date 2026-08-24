FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_investigation_agent/ ./veripay_investigation_agent/
EXPOSE 8000
CMD ["uvicorn", "veripay_investigation_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
