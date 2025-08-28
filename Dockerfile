# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install OS dependencies (needed for OpenCV etc.)
RUN apt-get update && apt-get install -y \
    git \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download CLIP model (optional, prevents downloading at runtime)
RUN python3 -c "import clip; clip.load('ViT-L/14@336px', device='cpu')"

# Copy source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 8000

# Run the FastAPI app
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
