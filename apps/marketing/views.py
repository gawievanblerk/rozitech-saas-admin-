"""
Marketing website views
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json

from apps.services.models import Service, ServiceCategory
from apps.subscriptions.models import PricingPlan


def homepage(request):
    """Landing page"""
    context = {
        'page_title': 'Rozitech - Enterprise SaaS Solutions for Modern Business',
        'meta_description': 'Transform your business operations with our comprehensive multi-tenant platform. Built for insurance companies, designed for growth, optimized for South Africa.'
    }
    return render(request, 'marketing/index.html', context)


def get_started(request):
    """Get Started / Pricing page"""
    context = {
        'page_title': 'Get Started - Rozitech Insurr Platform',
        'meta_description': 'Choose your plan and transform your insurance operations today. Starter, Professional, and Enterprise plans available.'
    }
    return render(request, 'marketing/get-started.html', context)


def learn_more(request):
    """Learn More / Product Information page"""
    context = {
        'page_title': 'Learn More - Rozitech Insurr Platform',
        'meta_description': 'Discover how our comprehensive insurance management platform transforms the way insurance companies operate.'
    }
    return render(request, 'marketing/learn-more.html', context)


def pricing(request):
    """Pricing page"""
    context = {
        'pricing_plans': PricingPlan.objects.filter(is_active=True).order_by('monthly_price'),
        'services': Service.objects.filter(is_public=True, status='active'),
        'page_title': 'Pricing - Rozitech SaaS Platform',
        'meta_description': 'Transparent pricing for businesses of all sizes. Start free and scale as you grow.'
    }
    return render(request, 'marketing/pricing.html', context)


def features(request):
    """Features page"""
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related('services')
    context = {
        'service_categories': categories,
        'page_title': 'Features - Rozitech SaaS Platform',
        'meta_description': 'Explore our comprehensive suite of business tools and services.'
    }
    return render(request, 'marketing/features.html', context)


def about(request):
    """About page"""
    context = {
        'page_title': 'About Us - Rozitech SaaS Platform',
        'meta_description': 'Learn about our mission to empower businesses with scalable SaaS solutions.'
    }
    return render(request, 'marketing/about.html', context)


def contact(request):
    """Contact page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        company = request.POST.get('company', '')
        message = request.POST.get('message')
        
        if name and email and message:
            # Send email to your team
            try:
                send_mail(
                    subject=f'Contact Form: {name} from {company or "Unknown Company"}',
                    message=f'Name: {name}\nEmail: {email}\nCompany: {company}\n\nMessage:\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for your message! We\'ll get back to you soon.')
                return redirect('marketing:contact')
            except Exception as e:
                messages.error(request, 'Sorry, there was an error sending your message. Please try again.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'page_title': 'Contact Us - Rozitech SaaS Platform',
        'meta_description': 'Get in touch with our team for support, sales inquiries, or partnerships.'
    }
    return render(request, 'marketing/contact.html', context)


def demo(request):
    """Demo request page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        company = request.POST.get('company')
        phone = request.POST.get('phone', '')
        use_case = request.POST.get('use_case', '')
        
        if name and email and company:
            # Send demo request email
            try:
                send_mail(
                    subject=f'Demo Request: {name} from {company}',
                    message=f'Name: {name}\nEmail: {email}\nCompany: {company}\nPhone: {phone}\n\nUse Case:\n{use_case}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.SALES_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Demo requested! Our sales team will contact you within 24 hours.')
                return redirect('marketing:demo')
            except Exception as e:
                messages.error(request, 'Sorry, there was an error processing your request. Please try again.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'page_title': 'Request Demo - Rozitech SaaS Platform',
        'meta_description': 'See our platform in action. Schedule a personalized demo with our team.'
    }
    return render(request, 'marketing/demo.html', context)


@csrf_exempt
def newsletter_signup(request):
    """Newsletter signup (AJAX endpoint)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if email:
                # Here you would integrate with your email service
                # (Mailchimp, ConvertKit, etc.)
                
                # For now, just send notification email
                send_mail(
                    subject='New Newsletter Signup',
                    message=f'New signup: {email}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.MARKETING_EMAIL],
                    fail_silently=True,
                )
                
                return JsonResponse({'success': True, 'message': 'Thanks for subscribing!'})
            else:
                return JsonResponse({'success': False, 'message': 'Email is required'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error processing request'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def legal_privacy(request):
    """Privacy policy"""
    context = {
        'page_title': 'Privacy Policy - Rozitech SaaS Platform',
        'meta_description': 'Our commitment to protecting your privacy and data.'
    }
    return render(request, 'marketing/legal/privacy.html', context)


def legal_terms(request):
    """Terms of service"""
    context = {
        'page_title': 'Terms of Service - Rozitech SaaS Platform',
        'meta_description': 'Terms and conditions for using our platform.'
    }
    return render(request, 'marketing/legal/terms.html', context)


def legal_security(request):
    """Security page"""
    context = {
        'page_title': 'Security - Rozitech SaaS Platform',
        'meta_description': 'Learn about our enterprise-grade security measures and compliance.'
    }
    return render(request, 'marketing/legal/security.html', context)