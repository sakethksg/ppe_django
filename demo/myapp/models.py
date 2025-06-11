from django.db import models
import os
from django.conf import settings

class UploadedImage(models.Model):
    original_image = models.ImageField(upload_to='uploads/')
    processed_image = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    detection_results = models.JSONField(null=True, blank=True)
    
    @property
    def processed_image_url(self):
        if self.processed_image:
            url = os.path.join(settings.MEDIA_URL, self.processed_image)
            # Normalize the URL path separators for web
            return url.replace('\\', '/')
        return None

    def __str__(self):
        return f"Image uploaded at {self.uploaded_at}"
    
    def delete(self, *args, **kwargs):
        # Delete the original image file
        if self.original_image:
            if os.path.isfile(self.original_image.path):
                os.remove(self.original_image.path)
        
        # Delete the processed image directory
        if self.processed_image:
            output_dir = os.path.join(settings.MEDIA_ROOT, 'outputs', str(self.id))
            if os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(output_dir)
        
        super().delete(*args, **kwargs)
