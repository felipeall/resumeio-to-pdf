FROM python:3.9-slim-bullseye

# Instantiate environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Install git
RUN apt-get update  \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . ./

# Run app
EXPOSE 8000
CMD ["python", "app/main.py"]