#!/usr/bin/env python3
"""
Production readiness test script
Tests key functionality in a production-like environment
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ppe_project.settings')
os.environ.setdefault('DJANGO_DEBUG', 'False')
os.environ.setdefault('YOLO_CONFIG_DIR', '/tmp')
os.environ.setdefault('OPENCV_LOG_LEVEL', 'ERROR')

def test_imports():
    """Test that all critical imports work"""
    print("🔍 Testing imports...")
    try:
        import django
        print("  ✅ Django import successful")
        
        import ultralytics
        print("  ✅ Ultralytics import successful")
        
        import cv2
        print("  ✅ OpenCV import successful")
        
        import torch
        print("  ✅ PyTorch import successful")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_django_setup():
    """Test Django configuration"""
    print("\n🔍 Testing Django setup...")
    try:
        import django
        django.setup()
        
        from django.conf import settings
        print(f"  ✅ Django settings loaded")
        print(f"  ✅ Debug mode: {settings.DEBUG}")
        print(f"  ✅ Media root: {settings.MEDIA_ROOT}")
        
        return True
    except Exception as e:
        print(f"  ❌ Django setup failed: {e}")
        return False

def test_yolo_model():
    """Test YOLO model loading"""
    print("\n🔍 Testing YOLO model...")
    try:
        from ultralytics import YOLO
        from django.conf import settings
        
        if hasattr(settings, 'YOLO_MODEL_PATH') and os.path.exists(settings.YOLO_MODEL_PATH):
            model = YOLO(settings.YOLO_MODEL_PATH)
            print("  ✅ Custom YOLO model loaded")
        else:
            model = YOLO('yolov8n.pt')
            print("  ✅ Default YOLO model loaded")
        
        # Test inference
        import numpy as np
        test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        results = model(test_image)
        print("  ✅ Model inference test successful")
        
        return True
    except Exception as e:
        print(f"  ❌ YOLO test failed: {e}")
        return False

def test_system_check():
    """Run Django system check"""
    print("\n🔍 Running Django system check...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'check_system'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("  ✅ System check passed")
            return True
        else:
            print(f"  ❌ System check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ System check error: {e}")
        return False

def test_server_startup():
    """Test that the server can start"""
    print("\n🔍 Testing server startup...")
    try:
        # Start server in background
        server_process = subprocess.Popen([
            sys.executable, 'manage.py', 'runserver', '127.0.0.1:8001', '--noreload'
        ], cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        
        # Test if server is responding
        try:
            response = requests.get('http://127.0.0.1:8001/', timeout=10)
            if response.status_code == 200:
                print("  ✅ Server started and responding")
                success = True
            else:
                print(f"  ❌ Server returned status code: {response.status_code}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Server not responding: {e}")
            success = False
        
        # Clean up
        server_process.terminate()
        server_process.wait(timeout=10)
        
        return success
    except Exception as e:
        print(f"  ❌ Server startup test failed: {e}")
        return False

def main():
    """Run all production readiness tests"""
    print("🚀 PPE Detection System - Production Readiness Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_django_setup,
        test_yolo_model,
        test_system_check,
        test_server_startup,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is production ready!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
