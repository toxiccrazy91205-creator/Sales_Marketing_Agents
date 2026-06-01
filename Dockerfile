FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Run collectstatic during build
RUN python manage.py collectstatic --no-input

EXPOSE 10000

# Run migrations and start gunicorn
CMD python manage.py migrate && gunicorn lead_gen_project.wsgi:application --bind 0.0.0.0:${PORT:-10000}
