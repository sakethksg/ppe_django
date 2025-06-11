# Use a lightweight Python base image
FROM python:3.9-slim-buster

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME=/app

# Set the working directory in the container
WORKDIR $APP_HOME

# Install system dependencies needed for Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt $APP_HOME/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . $APP_HOME

# Expose the port your Django application will run on
EXPOSE 8000

# Collect static files
RUN python manage.py collectstatic --noinput

# Command to run the application using Gunicorn
CMD ["gunicorn", "ppe_project.wsgi:application", "--bind", "0.0.0.0:8000"] 