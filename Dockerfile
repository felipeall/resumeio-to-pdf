FROM python:3.9.16-slim-buster

# Update, install curl & tesseract, clean up
RUN apt-get update  \
    && apt-get install -y  \
    curl \
    tesseract-ocr \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Install uv
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

# Install dependencies
WORKDIR /app
COPY requirements.txt ./
RUN /root/.cargo/bin/uv pip install --system --no-cache -r requirements.txt
COPY . ./

# Run app
EXPOSE 8000
CMD [ "python", "app/main.py" ]
