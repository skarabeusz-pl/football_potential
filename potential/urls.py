from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Example path for the root URL
    path('upload/', views.upload_image, name='upload_image'),
    # Add other paths as needed
]
