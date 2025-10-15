FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ReportLab
RUN apt-get update && apt-get install -y \
    gcc \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY ./src/microservices/reports/ .

# Expose port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8090/health || exit 1

# Run the service
CMD ["python", "report_service.py"]
