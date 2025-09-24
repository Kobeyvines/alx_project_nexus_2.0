# Use a slim Python image
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies (needed for psycopg2 & Pillow)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy project files
COPY . .

# Collect static files (in case you serve them)
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Use Gunicorn instead of runserver
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
