from django.urls import path
from . import views
from . import simple_views

urlpatterns = [
    path('', simple_views.simple_health_check, name='health_check'),
    path('full/', views.health_check, name='health_check_full'),
    path('auth-server-status/', views.auth_server_status, name='auth_server_status'),
]