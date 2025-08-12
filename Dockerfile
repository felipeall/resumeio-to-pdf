FROM python:3.10-slim-bullseye

# Update apt sources, install Tesseract, and clean up
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

# Set working directory
WORKDIR /app

# Copy requirements first (for caching layers)
COPY requirements.txt ./

# Install Python dependencies using uv
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install --system --no-cache -r requirements.txt

# Copy the rest of the application
COPY . ./

# Expose the application port
EXPOSE 8000

# Run the main application
CMD ["python", "app/main.py"]
