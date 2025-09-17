"""
URL configuration for payment processing
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'payments'

# API Router for future ViewSets
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]