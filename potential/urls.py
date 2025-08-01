from django.urls import path
from . import views
from .views import clear_all_data, show_potential


urlpatterns = [
    path('hello/', views.say_hello),
    path('', views.index, name='index'),  # Home page
    path('upload/<int:player_id>/', views.upload_image, name='upload_image'),
    path('show_potential/<int:player_id>/', views.show_potential, name='show_potential'),
    path('potential/clear_all/<int:player_id>/', clear_all_data, name='clear_all_data'),
    path('potential/<int:player_id>/', show_potential, name='show_potential'),
    path('potential/<int:player_id>/clear/', clear_all_data, name='clear_all_data'),
    # Add other paths as needed
]
