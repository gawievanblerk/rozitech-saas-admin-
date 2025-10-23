"""
Subscription management views
"""
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

from apps.subscriptions.services.stripe_service import StripeService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events

    This endpoint receives webhook events from Stripe and processes them
    using the StripeService.

    Stripe will send events like:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    - payment_method.attached
    - payment_method.detached
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    if not sig_header:
        logger.warning('Stripe webhook received without signature')
        return JsonResponse({'error': 'Missing signature'}, status=400)

    try:
        # Initialize Stripe service
        stripe_service = StripeService()

        # Verify and construct the event
        event = stripe_service.construct_webhook_event(payload, sig_header)

        # Handle the event
        success = stripe_service.handle_webhook_event(event)

        if success:
            logger.info(f"Successfully processed webhook event: {event['type']}")
            return JsonResponse({
                'status': 'success',
                'event_type': event['type']
            })
        else:
            logger.warning(f"Webhook event not handled: {event['type']}")
            return JsonResponse({
                'status': 'ignored',
                'event_type': event['type']
            })

    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JsonResponse({'error': 'Processing failed'}, status=500)


@require_POST
def test_stripe_connection(request):
    """
    Test endpoint to verify Stripe connection
    Admin/internal use only
    """
    try:
        stripe_service = StripeService()
        return JsonResponse({
            'status': 'success',
            'test_mode': stripe_service.test_mode,
            'message': 'Stripe connection successful'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)