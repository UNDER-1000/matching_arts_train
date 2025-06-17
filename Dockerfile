# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app


# Install OS dependencies (includes fix for OpenCV error)
RUN apt-get update && apt-get install -y \
    git \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision
RUN pip install --no-cache-dir -r requirements.txt
# Force reinstall the correct version
RUN pip install --no-cache-dir scikit-learn==1.6.1 --force-reinstall

RUN python3 -c "import clip; clip.load('ViT-L/14@336px', device='cpu')"

# Copy source code
COPY . .

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
