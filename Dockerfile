FROM python:3.12.11-slim-trixie

# Update, install tesseract, clean up
RUN apt-get update  \
    && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app:${PYTHONPATH}" \
    UV_SYSTEM_PYTHON=1

# Install dependencies
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install .

# Copy app files
COPY . ./

# Run app
EXPOSE 8000
CMD [ "python", "app/main.py" ]
