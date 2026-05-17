FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY productivity_kit ./productivity_kit
COPY public ./public
COPY examples ./examples

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "productivity_kit.api:app", "--host", "0.0.0.0", "--port", "8000"]
