from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title

class UploadedImage(models.Model):
    original_image = models.ImageField(upload_to='uploads/')
    processed_image = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    detection_results = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Image uploaded at {self.uploaded_at}"
