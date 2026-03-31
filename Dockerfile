FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create required folders
RUN mkdir -p static/uploads/radiology static/uploads/pathology data

# Start with Gunicorn (IMPORTANT)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"]
