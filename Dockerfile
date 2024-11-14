FROM python:3.9.16-slim-buster

# Update, install tesseract, clean up
RUN apt-get update  \
    && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Install dependencies
WORKDIR /app
COPY requirements.txt ./
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install --system --no-cache -r requirements.txt

# Copy app files
COPY . ./

# Run app
EXPOSE 8000
CMD [ "python", "app/main.py" ]
