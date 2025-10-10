# Use Python 3.11 slim image
FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/microservices/tasks/ .
# Also copy email service for sending notification emails
COPY src/microservices/notifications/email_service.py ../notifications/

# Expose port for unified task service
EXPOSE 8080
