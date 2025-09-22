# Use Python 3.11 slim image
FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/microservices/users/ .

# Expose port for user service
EXPOSE 8081