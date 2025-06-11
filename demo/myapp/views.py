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

# Load YOLO Model
try:
    model = YOLO(settings.YOLO_MODEL_PATH)
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
            if not uploaded_file.content_type.startswith('image/'):
                return render(request, 'myapp/upload_file.html', {'error': 'Only image files are allowed'})

            # Create new UploadedImage instance
            uploaded_image = UploadedImage(original_image=uploaded_file)
            uploaded_image.save()

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
                logger.info(f"Found processed image at {relative_path}")

                return render(request, 'myapp/upload_file.html', {
                    'success': 'File uploaded and processed successfully',
                    'input_file': uploaded_image.original_image.url,
                    'output_file': uploaded_image.processed_image_url
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
        return render(request, 'myapp/file_list.html', {
            'uploaded_images': uploaded_images
        })
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return render(request, 'myapp/file_list.html', {'error': f'Error listing files: {str(e)}'})

def gen_frames():
    video_capture = None
    try:
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            logger.error("Failed to open webcam")
            return

        while True:
            success, frame = video_capture.read()
            if not success:
                logger.error("Failed to read frame from webcam")
                break

            try:
                results = model(frame)
                for result in results:
                    for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                        x1, y1, x2, y2 = map(int, box[:4])
                        class_name = model.names[int(cls)]
                        confidence = round(float(conf), 2)

                        if class_name == 'helmet' and confidence < 0.7:
                            class_name = 'no helmet'

                        label = f'{class_name} {confidence}'
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

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

def webcam_prediction(request):
    if model is None:
        return render(request, 'myapp/webcam_view.html', {'error': 'Model not loaded. Please contact administrator.'})
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

def webcam_view(request):
    return render(request, 'myapp/webcam_view.html')
