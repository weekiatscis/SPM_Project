# Use Python 3.11 slim image
FROM python:3.11

WORKDIR /app

# Install wget for healthcheck
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/microservices/projects/ .

# Copy email service for notifications
RUN mkdir -p notifications
COPY src/microservices/notifications/email_service.py ./notifications/

# Expose port for project service
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8082/health || exit 1 