FROM python:3.12.13-slim

# Update, install Node.js for the rendering worker, clean up
RUN apt-get update  \
    && apt-get install -y --no-install-recommends \
    nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    UV_SYSTEM_PYTHON=true \
    UV_PROJECT_ENVIRONMENT="/usr/local"

# Install dependencies
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync --no-editable --frozen --no-dev

# Copy app files
COPY . ./

# Run app
EXPOSE 8000
CMD [ "python", "resumeio_to_pdf/main.py" ]
