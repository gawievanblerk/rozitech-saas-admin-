"""
URL configuration for subscription management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'subscriptions'

# API Router for future ViewSets
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]