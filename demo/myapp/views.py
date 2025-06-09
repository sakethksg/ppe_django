# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Book
# from .forms import BookForm

# # List view (Read)
# def book_list(request):
#     books = Book.objects.all()
#     return render(request, 'myapp/book_list.html', {'books': books})

# # Create view
# def book_create(request):
#     form = BookForm(request.POST or None)
#     if form.is_valid():
#         form.save()
#         return redirect('book_list')
#     return render(request, 'myapp/book_form.html', {'form': form})

# # Update view
# def book_update(request, pk):
#     book = get_object_or_404(Book, pk=pk)
#     form = BookForm(request.POST or None, instance=book)
#     if form.is_valid():
#         form.save()
#         return redirect('book_list')
#     return render(request, 'myapp/book_form.html', {'form': form})

# # Delete view
# def book_delete(request, pk):
#     book = get_object_or_404(Book, pk=pk)
#     if request.method == 'POST':
#         book.delete()
#         return redirect('book_list')
#     return render(request, 'myapp/book_confirm_delete.html', {'book': book})
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from ultralytics import YOLO
import os
from django.http import StreamingHttpResponse
import cv2
from .models import UploadedImage
import json

# Load YOLO Model
model = YOLO('myapp/media/best.pt')

def upload_file(request):
    if request.method == 'POST':
        try:
            if 'file' not in request.FILES:
                return render(request, 'myapp/upload_file.html', {'error': 'No file was uploaded'})

            uploaded_file = request.FILES['file']
            
            # Create UploadedImage instance
            uploaded_image = UploadedImage(original_image=uploaded_file)
            uploaded_image.save()

            # Get the path of the saved original image
            input_path = uploaded_image.original_image.path

            # Run YOLO prediction
            results = model.predict(source=input_path, save=True, project='myapp/media/outputs', name=str(uploaded_image.id))

            # Process the results
            detection_results = []
            for result in results:
                for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                    detection_results.append({
                        'class': model.names[int(cls)],
                        'confidence': float(conf),
                        'box': box.tolist()
                    })

            # Save detection results
            uploaded_image.detection_results = detection_results

            # Find the output image
            output_dir = os.path.join('myapp', 'media', 'outputs', str(uploaded_image.id), 'predict')
            if os.path.exists(output_dir):
                for f in os.listdir(output_dir):
                    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        output_path = os.path.join(output_dir, f)
                        # Save the processed image to the model
                        uploaded_image.processed_image = f'outputs/{uploaded_image.id}/predict/{f}'
                        uploaded_image.save()
                        break

            return render(request, 'myapp/upload_file.html', {
                'success': 'File uploaded and processed successfully',
                'input_file': uploaded_image.original_image.url,
                'output_file': uploaded_image.processed_image.url if uploaded_image.processed_image else None
            })

        except Exception as e:
            return render(request, 'myapp/upload_file.html', {'error': f'An error occurred: {str(e)}'})

    return render(request, 'myapp/upload_file.html')

def list_files(request):
    try:
        # Get all uploaded images from the database
        uploaded_images = UploadedImage.objects.all().order_by('-uploaded_at')
        
        return render(request, 'myapp/file_list.html', {
            'uploaded_images': uploaded_images
        })
    except Exception as e:
        return render(request, 'myapp/file_list.html', {'error': f'Error listing files: {str(e)}'})

def gen_frames():
    # Open the webcam (device 0 by default)
    video_capture = cv2.VideoCapture(0)
    while True:
        success, frame = video_capture.read()
        if not success:
            break
        else:
            # Perform YOLO prediction on the frame
            results = model(frame)  # Run YOLO inference
            
            # Iterate over the predictions and draw boxes with labels
            for result in results:
                for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                    x1, y1, x2, y2 = map(int, box[:4])  # Get bounding box coordinates
                    
                    # Get the class label and confidence score
                    class_name = model.names[int(cls)]  # Get the class name
                    confidence = round(float(conf), 2)  # Confidence score
                    
                    # Draw the bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Put the label (class name and confidence)
                    if(class_name=='helmet' and confidence<0.7):
                        class_name='no helmet'
                    label = f'{class_name} {confidence}'
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(frame, label, (x1, y1 - 10), font, 0.6, (0, 0, 0), 2)
            
            # Convert the frame to byte data for streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Yield the frame to the client
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def webcam_prediction(request):
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

def webcam_view(request):
    return render(request, 'myapp/webcam_view.html')

def index(request):
    return render(request, 'myapp/index.html')