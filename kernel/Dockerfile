FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/kernel

EXPOSE 8080

CMD ["uvicorn", "kernel.api:app", "--host", "0.0.0.0", "--port", "8080"]
