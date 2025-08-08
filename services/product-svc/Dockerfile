FROM python:3.11-slim

#set env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=5000

#create app dir
WORKDIR /app

#install sys dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

#install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#create non-root user
RUN useradd --create-home --shell /bin/bash app

COPY --chown=app:app . .

#switch to non-root user
USER app

#expose port
EXPOSE 5000

#healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
CMD python -c "import requests; requests.get('http://localhost:5000/health')"

#start app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
