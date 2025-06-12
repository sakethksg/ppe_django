# Use a more recent Python base image to avoid security vulnerabilities
FROM python:3.11-slim

# Install system dependencies including camera and video support
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-dev \
    libv4l-dev \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME=/app
ENV YOLO_CONFIG_DIR=/tmp
ENV OPENCV_LOG_LEVEL=ERROR

# Set the working directory in the container
WORKDIR $APP_HOME

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt $APP_HOME/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . $APP_HOME

# Create necessary directories
RUN mkdir -p static media templates /tmp/.yolo_config
RUN chmod -R 777 /tmp/.yolo_config

# Run setup script to ensure YOLO model is available
RUN python setup_model.py

# Collect static files
RUN python manage.py collectstatic --noinput

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting PPE Detection System..."\n\
python manage.py check_system\n\
python manage.py migrate\n\
python manage.py collectstatic --noinput\n\
echo "Starting web server..."\n\
gunicorn ppe_project.wsgi:application --bind 0.0.0.0:8000 --timeout 120 --workers 1' > /app/start.sh && \
chmod +x /app/start.sh

# Expose the port your Django application will run on
EXPOSE 8000

# Start command
CMD ["/app/start.sh"] 