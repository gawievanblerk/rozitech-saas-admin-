"""
URL configuration for authentication API endpoints
"""
from django.urls import path
from apps.authentication import views

app_name = 'authentication'

urlpatterns = [
    # Token verification endpoint
    path('verify', views.TokenVerificationView.as_view(), name='verify-token'),
]