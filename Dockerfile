FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 0.0.0.0 is container-internal; docker-compose publishes it on 127.0.0.1 only.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
