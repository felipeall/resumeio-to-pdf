FROM python:3.9-slim-bookworm

# Обновление пакетов, установка tesseract, очистка кешей
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Установка зависимостей
WORKDIR /app
COPY requirements.txt ./
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install --system --no-cache -r requirements.txt

# Копирование файлов приложения
COPY . ./

# Открытый порт
EXPOSE 8000

# Запуск приложения
CMD [ "python", "app/main.py" ]
