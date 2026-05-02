FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Update, install tesseract, clean up
RUN apt-get update  \
    && apt-get install -y --no-install-recommends \
    tesseract-ocr \
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
RUN uv sync --no-editable --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

# Copy app files
COPY . .

# Run app
EXPOSE 8000
CMD [ "python", "main.py" ]
