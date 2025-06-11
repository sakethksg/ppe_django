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

# Expose the port your Django application will run on
EXPOSE 8000

# Command to run the application using Gunicorn
CMD ["gunicorn", "ppe_project.wsgi:application", "--bind", "0.0.0.0:8000"] 