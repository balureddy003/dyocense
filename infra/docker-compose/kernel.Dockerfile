# syntax=docker/dockerfile:1.5

FROM python:3.13-slim AS base

WORKDIR /app

COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY services ./services
COPY packages ./packages

ENV PYTHONPATH=/app
CMD ["uvicorn", "services.kernel.main:app", "--host", "0.0.0.0", "--port", "8001"]
