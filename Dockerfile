FROM python:3.9-slim-bullseye

# Update, install tesseract and clean up
RUN apt-get update  \
    && apt-get install -y tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.6.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache
ENV PATH="${PATH}:${POETRY_VENV}/bin"
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Install poetry
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Install dependencies
WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --only main

# Run app
COPY . ./
EXPOSE 8000
CMD [ "poetry", "run", "python", "app/main.py" ]
