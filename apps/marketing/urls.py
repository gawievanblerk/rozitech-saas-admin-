"""
Marketing website URLs
"""
from django.urls import path
from apps.marketing import views

app_name = 'marketing'

urlpatterns = [
    # Main marketing pages
    path('', views.homepage, name='homepage'),
    path('get-started/', views.get_started, name='get_started'),
    path('learn-more/', views.learn_more, name='learn_more'),
    path('pricing/', views.pricing, name='pricing'),
    path('features/', views.features, name='features'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('demo/', views.demo, name='demo'),
    
    # AJAX endpoints
    path('api/newsletter/', views.newsletter_signup, name='newsletter_signup'),
    
    # Legal pages
    path('privacy/', views.legal_privacy, name='privacy'),
    path('terms/', views.legal_terms, name='terms'),
    path('security/', views.legal_security, name='security'),
]