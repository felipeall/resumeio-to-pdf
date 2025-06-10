FROM python:3.9.16-slim-buster

# Update and install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    tesseract-ocr curl \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Install uv package manager
RUN curl -sSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR /app

# Copy dependency list
COPY requirements.txt ./

# Use uv or pip to install dependencies
RUN if command -v uv >/dev/null 2>&1; then \
        uv pip install --system --no-cache -r requirements.txt ; \
    else \
        pip install --no-cache-dir -r requirements.txt ; \
    fi

# Copy app source code
COPY . ./

# Expose port and run
EXPOSE 8000
CMD ["python", "app/main.py"]
