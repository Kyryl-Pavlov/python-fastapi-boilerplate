FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY services/app/app/ app/
COPY migrations/ migrations/
COPY alembic.ini .
COPY wsgi.py .

RUN addgroup --system app && adduser --system --ingroup app app
ENV HOME=/tmp
USER app

EXPOSE 5000

CMD ["uvicorn", "wsgi:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]
