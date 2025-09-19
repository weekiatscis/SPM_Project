# Use Python 3.11 slim image
FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/microservices/tasks/ .

# Expose ports for both services
EXPOSE 8080 8081
