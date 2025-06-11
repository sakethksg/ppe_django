from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('files/', views.list_files, name='list_files'),
    path('webcam/', views.webcam_view, name='webcam_view'),
    path('webcam_feed/', views.webcam_prediction, name='webcam_prediction'),
    path('upload/', views.upload_file, name='upload_file'),
]
