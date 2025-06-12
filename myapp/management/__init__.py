"""
Management command to check system readiness for PPE detection
"""

import os
import cv2
from django.core.management.base import BaseCommand
from django.conf import settings
from ultralytics import YOLO


class Command(BaseCommand):
    help = 'Check system readiness for PPE detection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose', 
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('=== PPE Detection System Check ===\n'))
        
        # Check YOLO model
        self.check_yolo_model(verbose)
        
        # Check camera availability
        self.check_camera(verbose)
        
        # Check directories
        self.check_directories(verbose)
        
        # Check environment variables
        self.check_environment(verbose)
        
        self.stdout.write(self.style.SUCCESS('\n=== System Check Complete ==='))

    def check_yolo_model(self, verbose):
        self.stdout.write(self.style.SUCCESS('1. Checking YOLO Model...'))
        
        try:
            if hasattr(settings, 'YOLO_MODEL_PATH'):
                model_path = settings.YOLO_MODEL_PATH
                if verbose:
                    self.stdout.write(f'   Model path: {model_path}')
                
                if os.path.exists(model_path):
                    self.stdout.write(self.style.SUCCESS('   ✓ Model file exists'))
                    
                    # Try to load the model
                    try:
                        model = YOLO(model_path)
                        self.stdout.write(self.style.SUCCESS('   ✓ Model loads successfully'))
                        if verbose:
                            self.stdout.write(f'   Model classes: {list(model.names.values())}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'   ✗ Model loading failed: {e}'))
                else:
                    self.stdout.write(self.style.WARNING('   ⚠ Model file not found, trying default...'))
                    try:
                        model = YOLO('yolov8n.pt')
                        self.stdout.write(self.style.SUCCESS('   ✓ Default model loaded'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'   ✗ Default model failed: {e}'))
            else:
                self.stdout.write(self.style.ERROR('   ✗ YOLO_MODEL_PATH not configured'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ YOLO check failed: {e}'))

    def check_camera(self, verbose):
        self.stdout.write(self.style.SUCCESS('\n2. Checking Camera Access...'))
        
        camera_found = False
        for i in range(3):  # Check first 3 camera indices
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        camera_found = True
                        self.stdout.write(self.style.SUCCESS(f'   ✓ Camera {i} is available'))
                        if verbose:
                            height, width = frame.shape[:2]
                            self.stdout.write(f'     Resolution: {width}x{height}')
                    cap.release()
                elif verbose:
                    self.stdout.write(f'   - Camera {i} not available')
            except Exception as e:
                if verbose:
                    self.stdout.write(f'   - Camera {i} error: {e}')
        
        if not camera_found:
            self.stdout.write(self.style.WARNING('   ⚠ No cameras found (this is expected in containerized environments)'))

    def check_directories(self, verbose):
        self.stdout.write(self.style.SUCCESS('\n3. Checking Directories...'))
        
        required_dirs = [
            settings.MEDIA_ROOT,
            os.path.join(settings.MEDIA_ROOT, 'uploads'),
            os.path.join(settings.MEDIA_ROOT, 'outputs'),
        ]
        
        if hasattr(settings, 'YOLO_CONFIG_DIR'):
            required_dirs.append(settings.YOLO_CONFIG_DIR)
        
        for directory in required_dirs:
            if os.path.exists(directory):
                self.stdout.write(self.style.SUCCESS(f'   ✓ {directory}'))
                if verbose:
                    # Check write permissions
                    try:
                        test_file = os.path.join(directory, 'test_write.tmp')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        self.stdout.write('     (writable)')
                    except:
                        self.stdout.write(self.style.WARNING('     (not writable)'))
            else:
                self.stdout.write(self.style.ERROR(f'   ✗ Missing: {directory}'))

    def check_environment(self, verbose):
        self.stdout.write(self.style.SUCCESS('\n4. Checking Environment...'))
        
        env_vars = [
            'YOLO_CONFIG_DIR',
            'OPENCV_LOG_LEVEL',
            'DJANGO_DEBUG',
            'DJANGO_SECRET_KEY',
        ]
        
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                if verbose or var in ['YOLO_CONFIG_DIR', 'OPENCV_LOG_LEVEL']:
                    if var == 'DJANGO_SECRET_KEY':
                        self.stdout.write(f'   ✓ {var}: {"*" * len(value)}')
                    else:
                        self.stdout.write(f'   ✓ {var}: {value}')
                else:
                    self.stdout.write(f'   ✓ {var}')
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠ {var} not set'))
