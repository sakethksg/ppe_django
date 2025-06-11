# Use a lightweight Python base image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME=/app

# Set the working directory in the container
WORKDIR $APP_HOME

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt $APP_HOME/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . $APP_HOME

# Create necessary directories
RUN mkdir -p static media templates

# Collect static files
RUN python manage.py collectstatic --noinput

# Create startup script
RUN echo '#!/bin/bash\n\
python manage.py migrate\n\
python manage.py collectstatic --noinput\n\
gunicorn ppe_project.wsgi:application --bind 0.0.0.0:8000' > /app/start.sh && \
chmod +x /app/start.sh

# Expose the port your Django application will run on
EXPOSE 8000

# Start command
CMD ["/app/start.sh"] 