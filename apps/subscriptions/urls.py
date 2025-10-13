"""
URL configuration for subscription management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.authentication.views import SubscriptionCheckView
from . import views

app_name = 'subscriptions'

# API Router for future ViewSets
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),

    # TeamSpace SSO integration endpoint
    path('check', SubscriptionCheckView.as_view(), name='subscription-check'),

    # Stripe webhook endpoint
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),

    # Test endpoints (internal use)
    path('test/stripe/', views.test_stripe_connection, name='test-stripe'),
]