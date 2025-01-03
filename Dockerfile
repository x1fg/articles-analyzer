FROM python:3.12.3-slim
RUN apt-get update && apt-get install -y \
    libpq-dev gcc cron --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
RUN echo "0 3 * * * python /app/main.py parser >> /app/logs/parser.log 2>&1" > /etc/cron.d/parser_cron
RUN chmod 0644 /etc/cron.d/parser_cron
CMD ["sh", "-c", "cron && python main.py bot"]