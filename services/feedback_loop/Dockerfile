FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY veripay_feedback_loop/ ./veripay_feedback_loop/
EXPOSE 8000
CMD ["uvicorn", "veripay_feedback_loop.main:app", "--host", "0.0.0.0", "--port", "8000"]
