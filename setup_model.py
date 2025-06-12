#!/usr/bin/env python3
"""
Script to ensure YOLO model is available
This script checks if the YOLO model exists and downloads it if necessary
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ppe_project.settings')

import django
django.setup()

from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_yolo_model():
    """Ensure YOLO model is available"""
    try:
        from ultralytics import YOLO
        
        # Check if custom model exists
        if hasattr(settings, 'YOLO_MODEL_PATH') and os.path.exists(settings.YOLO_MODEL_PATH):
            logger.info(f"YOLO model found at: {settings.YOLO_MODEL_PATH}")
            # Test loading the model
            model = YOLO(settings.YOLO_MODEL_PATH)
            logger.info("Custom YOLO model loaded successfully")
            return True
        
        # Download default model if custom model not found
        logger.info("Custom model not found, downloading default YOLOv8n model...")
        model = YOLO('yolov8n.pt')  # This will download the model
        
        # Save the model to the expected location
        model_dir = os.path.dirname(settings.YOLO_MODEL_PATH)
        os.makedirs(model_dir, exist_ok=True)
        
        # Copy the downloaded model to the expected location
        import shutil
        default_model_path = os.path.join(os.path.expanduser('~'), '.ultralytics', 'models', 'yolov8n.pt')
        if os.path.exists(default_model_path):
            shutil.copy2(default_model_path, settings.YOLO_MODEL_PATH)
            logger.info(f"Model copied to: {settings.YOLO_MODEL_PATH}")
        
        logger.info("YOLO model setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup YOLO model: {str(e)}")
        return False

def setup_directories():
    """Create necessary directories"""
    try:
        # Create media directories
        media_dirs = [
            settings.MEDIA_ROOT,
            os.path.join(settings.MEDIA_ROOT, 'uploads'),
            os.path.join(settings.MEDIA_ROOT, 'outputs'),
        ]
        
        for directory in media_dirs:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Create YOLO config directory
        if hasattr(settings, 'YOLO_CONFIG_DIR'):
            os.makedirs(settings.YOLO_CONFIG_DIR, exist_ok=True)
            logger.info(f"Created YOLO config directory: {settings.YOLO_CONFIG_DIR}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create directories: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting PPE Detection setup...")
    
    # Setup directories
    if not setup_directories():
        sys.exit(1)
    
    # Setup YOLO model
    if not setup_yolo_model():
        sys.exit(1)
    
    logger.info("Setup completed successfully!")
