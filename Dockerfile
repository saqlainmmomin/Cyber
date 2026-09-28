FROM python:3.13-slim

WORKDIR /app

# P6-8: WeasyPrint (board report v2 PDF) needs Pango and HarfBuzz at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 0.0.0.0 is container-internal; docker-compose publishes it on 127.0.0.1 only.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
