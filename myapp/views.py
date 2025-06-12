from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from ultralytics import YOLO
import os
import cv2
import json
import logging
from django.conf import settings
from django.http import StreamingHttpResponse
from .models import UploadedImage

# Set up logging
logger = logging.getLogger(__name__)

# Load YOLO Model with better error handling
model = None
try:
    if hasattr(settings, 'YOLO_MODEL_PATH') and os.path.exists(settings.YOLO_MODEL_PATH):
        logger.info(f"Loading YOLO model from: {settings.YOLO_MODEL_PATH}")
        model = YOLO(settings.YOLO_MODEL_PATH)
        logger.info("YOLO model loaded successfully")
    else:
        logger.warning(f"YOLO model file not found at: {getattr(settings, 'YOLO_MODEL_PATH', 'Not specified')}")
        # Try to download a default model
        try:
            logger.info("Attempting to download default YOLOv8n model...")
            model = YOLO('yolov8n.pt')  # This will download the model if not present
            logger.info("Default YOLOv8n model loaded successfully")
        except Exception as download_error:
            logger.error(f"Failed to download default model: {str(download_error)}")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {str(e)}")
    model = None

def index(request):
    return render(request, 'myapp/index.html')

def upload_file(request):
    if request.method == 'POST':
        try:
            if model is None:
                return render(request, 'myapp/upload_file.html', {'error': 'Model not loaded. Please contact administrator.'})

            if 'file' not in request.FILES:
                return render(request, 'myapp/upload_file.html', {'error': 'No file was uploaded'})

            uploaded_file = request.FILES['file']
            
            # Validate file type
            if not uploaded_file.content_type.startswith('image/'):
                return render(request, 'myapp/upload_file.html', {'error': 'Only image files are allowed'})
            
            # Validate file size (10MB limit)
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB in bytes
                return render(request, 'myapp/upload_file.html', {'error': 'File size exceeds 10MB limit'})

            # Create new UploadedImage instance
            uploaded_image = UploadedImage(original_image=uploaded_file)
            uploaded_image.save()
            logger.info(f"Saved original image with ID: {uploaded_image.id}")

            try:
                # Set up output directory for this specific upload
                output_dir = os.path.join(settings.MEDIA_ROOT, 'outputs', str(uploaded_image.id))
                
                # Clean up any existing files for this upload
                if os.path.exists(output_dir):
                    for root, dirs, files in os.walk(output_dir, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(output_dir)
                
                # Create fresh output directory
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created output directory at {output_dir}")

                # Run prediction
                input_path = uploaded_image.original_image.path
                logger.info(f"Running prediction on image at: {input_path}")
                results = model.predict(source=input_path, save=True, project=output_dir)
                if not results:
                    raise Exception("No detection results generated")
                logger.info("Successfully ran YOLO prediction")

                # Process detection results
                detection_results = []
                for result in results:
                    for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                        detection_results.append({
                            'class': model.names[int(cls)],
                            'confidence': float(conf),
                            'box': box.tolist()
                        })
                uploaded_image.detection_results = detection_results
                logger.info(f"Processed detection results: {len(detection_results)} detections found")

                # Find the processed image
                predict_dir = os.path.join(output_dir, 'predict')
                if not os.path.exists(predict_dir):
                    logger.error(f"Predict directory not found at {predict_dir}")
                    raise Exception("Output directory not found after processing")

                # Get the first output image
                output_files = [f for f in os.listdir(predict_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if not output_files:
                    logger.error("No output image files found in predict directory")
                    raise Exception("No output image was generated")

                # Save the processed image path
                output_filename = output_files[0]
                relative_path = os.path.join('outputs', str(uploaded_image.id), 'predict', output_filename)
                uploaded_image.processed_image = relative_path
                uploaded_image.save()
                logger.info(f"Saved processed image path: {relative_path}")

                # Ensure the file exists before returning
                full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                if not os.path.exists(full_path):
                    logger.error(f"Processed image file not found at: {full_path}")
                    raise Exception("Processed image file not found after saving")

                logger.info(f"Found processed image at {full_path}")

                # Get the URLs for both images
                input_url = uploaded_image.original_image.url
                output_url = uploaded_image.processed_image_url
                logger.info(f"Input URL: {input_url}")
                logger.info(f"Output URL: {output_url}")

                # Return the response with the processed image
                return render(request, 'myapp/upload_file.html', {
                    'success': 'File uploaded and processed successfully',
                    'input_file': input_url,
                    'output_file': output_url
                })

            except Exception as e:
                logger.error(f"Error in YOLO processing: {str(e)}")
                uploaded_image.delete()
                return render(request, 'myapp/upload_file.html', {'error': f'Failed to process image: {str(e)}'})

        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}")
            return render(request, 'myapp/upload_file.html', {'error': f'An error occurred: {str(e)}'})

    return render(request, 'myapp/upload_file.html')

def list_files(request):
    try:
        uploaded_images = UploadedImage.objects.all().order_by('-uploaded_at')
        # Filter out images with missing files
        valid_images = []
        for image in uploaded_images:
            try:
                if image.original_image and os.path.exists(image.original_image.path):
                    valid_images.append(image)
                else:
                    # Delete the record if the file is missing
                    image.delete()
            except Exception as e:
                logger.error(f"Error checking image {image.id}: {str(e)}")
                continue
        
        return render(request, 'myapp/file_list.html', {
            'uploaded_images': valid_images
        })
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return render(request, 'myapp/file_list.html', {'error': f'Error listing files: {str(e)}'})

def gen_frames():
    video_capture = None
    try:
        # Try different camera backends and indices
        camera_backends = [
            (0, cv2.CAP_DSHOW),    # DirectShow (Windows)
            (0, cv2.CAP_V4L2),     # Video4Linux2 (Linux)
            (0, cv2.CAP_ANY),      # Auto-detect backend
            (1, cv2.CAP_ANY),      # Try camera index 1
            (2, cv2.CAP_ANY),      # Try camera index 2
        ]
        
        for camera_index, backend in camera_backends:
            try:
                logger.info(f"Trying camera index {camera_index} with backend {backend}")
                video_capture = cv2.VideoCapture(camera_index, backend)
                
                if video_capture.isOpened():
                    # Test if we can read a frame
                    ret, test_frame = video_capture.read()
                    if ret and test_frame is not None:
                        logger.info(f"Successfully opened camera {camera_index} with backend {backend}")
                        break
                    else:
                        video_capture.release()
                        video_capture = None
                else:
                    if video_capture:
                        video_capture.release()
                    video_capture = None
            except Exception as e:
                logger.warning(f"Failed to open camera {camera_index} with backend {backend}: {str(e)}")
                if video_capture:
                    video_capture.release()
                video_capture = None
                continue
        
        if video_capture is None or not video_capture.isOpened():
            logger.error("Failed to open any camera")
            # Generate a placeholder frame indicating no camera
            placeholder_frame = generate_no_camera_frame()
            while True:
                _, buffer = cv2.imencode('.jpg', placeholder_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                import time
                time.sleep(1)  # Update every second
            return

        # Set camera properties for better performance
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        video_capture.set(cv2.CAP_PROP_FPS, 30)

        while True:
            success, frame = video_capture.read()
            if not success:
                logger.error("Failed to read frame from webcam")
                break

            try:
                if model is not None:
                    results = model(frame)
                    for result in results:
                        if result.boxes is not None and len(result.boxes) > 0:
                            for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                                x1, y1, x2, y2 = map(int, box[:4])
                                class_name = model.names[int(cls)]
                                confidence = round(float(conf), 2)

                                if class_name == 'helmet' and confidence < 0.7:
                                    class_name = 'no helmet'

                                label = f'{class_name} {confidence}'
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                else:
                    # Add text indicating model not loaded
                    cv2.putText(frame, "YOLO Model Not Loaded", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                logger.error(f"Error processing frame: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Error in gen_frames: {str(e)}")
    finally:
        if video_capture is not None:
            video_capture.release()

def generate_no_camera_frame():
    """Generate a placeholder frame when no camera is available"""
    import numpy as np
    
    # Create a black frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add text
    cv2.putText(frame, "No Camera Available", (150, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    cv2.putText(frame, "Please check camera connection", (120, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "or try a different browser", (140, 280), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return frame

def webcam_prediction(request):
    if model is None:
        return render(request, 'myapp/webcam_view.html', {'error': 'Model not loaded. Please contact administrator.'})
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

def webcam_view(request):
    return render(request, 'myapp/webcam_view.html')
