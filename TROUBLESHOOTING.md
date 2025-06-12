# PPE Detection System - Troubleshooting Guide

## Common Issues and Solutions

### 1. YOLO Configuration Directory Warning

**Error:** 
```
WARNING ⚠️ user config directory '/root/.config/Ultralytics' is not writeable, defaulting to '/tmp' or CWD.
```

**Solution:**
This warning is now handled automatically by setting the `YOLO_CONFIG_DIR` environment variable. The system will use a writable temporary directory for YOLO configuration.

### 2. Camera Access Issues

**Error:**
```
[ WARN:0@49.856] global cap_v4l.cpp:913 open VIDEOIO(V4L2:/dev/video0): can't open camera by index
Failed to open webcam
```

**Possible Causes & Solutions:**

#### In Development (Local)
- **No camera connected**: Connect a webcam to your system
- **Camera in use**: Close other applications using the camera
- **Permissions**: On Linux, ensure your user is in the `video` group:
  ```bash
  sudo usermod -a -G video $USER
  ```
- **Browser permissions**: When accessing the web interface, allow camera access in your browser

#### In Production (Docker/Render)
- **Expected behavior**: Containerized environments typically don't have camera access
- **Solution**: The system now gracefully handles this by showing a "No Camera Available" message
- **Workaround**: Use the image upload feature instead of live detection

### 3. YOLO Model Loading Issues

**Error:**
```
Failed to load YOLO model: [Errno 2] No such file or directory: 'yolov8n.pt'
```

**Solution:**
1. The system will automatically download the default YOLOv8n model
2. For custom models, ensure the model file is in the correct location
3. Run the setup script manually:
   ```bash
   python setup_model.py
   ```

### 4. System Check Command

To diagnose issues, run the system check command:

```bash
# Basic check
python manage.py check_system

# Detailed check
python manage.py check_system --verbose
```

This will verify:
- YOLO model availability and loading
- Camera access (if available)
- Directory permissions
- Environment variables

### 5. Environment Variables

Ensure these environment variables are set appropriately:

| Variable | Purpose | Default |
|----------|---------|---------|
| `YOLO_CONFIG_DIR` | YOLO configuration directory | `/tmp` |
| `OPENCV_LOG_LEVEL` | OpenCV logging level | `ERROR` |
| `DJANGO_DEBUG` | Django debug mode | `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | `.onrender.com` |

### 6. Deployment on Render

The `render.yaml` configuration includes the necessary environment variables:

```yaml
envVars:
  - key: DJANGO_SECRET_KEY
    generateValue: true
  - key: DJANGO_DEBUG
    value: "False"
  - key: DJANGO_ALLOWED_HOSTS
    value: ".onrender.com"
```

### 7. Local Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up the model:**
   ```bash
   python setup_model.py
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Check system:**
   ```bash
   python manage.py check_system --verbose
   ```

5. **Start development server:**
   ```bash
   python manage.py runserver
   ```

### 8. Performance Optimization

For better performance in production:

- **Use a dedicated GPU server** for faster YOLO inference
- **Reduce camera resolution** in the webcam view (currently set to 640x480)
- **Adjust frame rate** in the JavaScript (currently 100ms intervals)
- **Use a more powerful instance** on Render (upgrade from free tier)

### 9. Security Considerations

- **Camera access**: The webcam feature attempts to access local cameras
- **File uploads**: Images are validated for type and size
- **CORS**: Consider adding CORS headers if accessing from different domains
- **HTTPS**: Use HTTPS in production for camera access

### 10. Feature Limitations

#### Current System Capabilities:
- ✅ Image upload and processing
- ✅ Gallery of processed images
- ✅ Webcam detection (when camera available)
- ✅ Dark mode support
- ✅ Responsive design

#### Known Limitations:
- ⚠️ Webcam access limited in containerized environments
- ⚠️ Single user access (no authentication system)
- ⚠️ Limited to specific PPE classes (helmet, vest, person, etc.)

## Getting Help

If you encounter issues not covered here:

1. Check the Django logs for detailed error messages
2. Run `python manage.py check_system --verbose` for diagnostics
3. Ensure all environment variables are properly set
4. Verify that all required dependencies are installed
