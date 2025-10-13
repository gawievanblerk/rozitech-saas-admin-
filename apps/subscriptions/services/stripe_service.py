"""
Stripe integration service for subscription management
"""
import stripe
from django.conf import settings
from django.db import transaction
from decimal import Decimal
from typing import Dict, Optional, List
import logging

from apps.products.models import Product, ProductPlan
from apps.subscriptions.models_products import ProductSubscription, UsageRecord
from apps.tenants.models import Organization
from apps.payments.models import PaymentProvider, PaymentMethod, Transaction

logger = logging.getLogger(__name__)


class StripeService:
    """
    Service for handling all Stripe API interactions
    """

    def __init__(self):
        """Initialize Stripe with API keys from settings"""
        self.api_key = getattr(settings, 'STRIPE_API_KEY', None)
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

        if not self.api_key:
            raise ValueError("STRIPE_API_KEY not configured in settings")

        stripe.api_key = self.api_key
        self.test_mode = self.api_key.startswith('sk_test_')

    # =================================================================
    # CUSTOMER MANAGEMENT
    # =================================================================

    def get_or_create_customer(self, organization: Organization) -> str:
        """
        Get existing Stripe customer or create new one for organization

        Args:
            organization: Organization model instance

        Returns:
            str: Stripe customer ID
        """
        # Check if organization already has a Stripe customer ID
        if hasattr(organization, 'stripe_customer_id') and organization.stripe_customer_id:
            try:
                # Verify the customer still exists in Stripe
                customer = stripe.Customer.retrieve(organization.stripe_customer_id)
                if not customer.get('deleted'):
                    return organization.stripe_customer_id
            except stripe.error.InvalidRequestError:
                # Customer no longer exists, will create new one
                pass

        # Create new Stripe customer
        try:
            customer = stripe.Customer.create(
                name=organization.name,
                email=organization.email if hasattr(organization, 'email') else None,
                metadata={
                    'organization_id': str(organization.id),
                    'organization_slug': organization.slug,
                    'environment': 'test' if self.test_mode else 'production'
                }
            )

            # Store Stripe customer ID on organization
            organization.stripe_customer_id = customer.id
            organization.save(update_fields=['stripe_customer_id'])

            logger.info(f"Created Stripe customer {customer.id} for organization {organization.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer for {organization.id}: {str(e)}")
            raise

    def update_customer(self, organization: Organization, **kwargs) -> Dict:
        """
        Update Stripe customer information

        Args:
            organization: Organization model instance
            **kwargs: Fields to update (name, email, etc.)

        Returns:
            Dict: Updated Stripe customer object
        """
        customer_id = self.get_or_create_customer(organization)

        try:
            customer = stripe.Customer.modify(customer_id, **kwargs)
            logger.info(f"Updated Stripe customer {customer_id}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update Stripe customer {customer_id}: {str(e)}")
            raise

    # =================================================================
    # PRODUCT & PRICE MANAGEMENT
    # =================================================================

    def sync_product_to_stripe(self, product: Product) -> str:
        """
        Create or update product in Stripe

        Args:
            product: Product model instance

        Returns:
            str: Stripe product ID
        """
        try:
            if product.metadata.get('stripe_product_id'):
                # Update existing product
                stripe_product = stripe.Product.modify(
                    product.metadata['stripe_product_id'],
                    name=product.name,
                    description=product.description,
                    metadata={
                        'product_code': product.code,
                        'product_id': str(product.id),
                        'billing_type': product.billing_type
                    }
                )
            else:
                # Create new product
                stripe_product = stripe.Product.create(
                    name=product.name,
                    description=product.description,
                    metadata={
                        'product_code': product.code,
                        'product_id': str(product.id),
                        'billing_type': product.billing_type
                    }
                )

                # Store Stripe product ID
                product.metadata['stripe_product_id'] = stripe_product.id
                product.save(update_fields=['metadata'])

            logger.info(f"Synced product {product.code} to Stripe: {stripe_product.id}")
            return stripe_product.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to sync product {product.code} to Stripe: {str(e)}")
            raise

    def sync_product_plan_to_stripe(self, product_plan: ProductPlan) -> str:
        """
        Create or update price in Stripe for a product plan

        Args:
            product_plan: ProductPlan model instance

        Returns:
            str: Stripe price ID
        """
        # Ensure product exists in Stripe
        stripe_product_id = self.sync_product_to_stripe(product_plan.product)

        try:
            # Convert price to cents
            unit_amount = int(product_plan.price * 100)

            # Determine recurring interval
            interval_map = {
                'monthly': 'month',
                'quarterly': 'month',
                'annually': 'year'
            }
            interval = interval_map.get(product_plan.billing_interval, 'month')
            interval_count = 3 if product_plan.billing_interval == 'quarterly' else 1

            # Create new price (Stripe prices are immutable)
            stripe_price = stripe.Price.create(
                product=stripe_product_id,
                unit_amount=unit_amount,
                currency=product_plan.currency.lower(),
                recurring={
                    'interval': interval,
                    'interval_count': interval_count
                },
                metadata={
                    'product_plan_id': str(product_plan.id),
                    'base_plan_id': str(product_plan.base_plan.id),
                    'plan_name': product_plan.base_plan.name
                }
            )

            # Store Stripe price ID
            product_plan.stripe_price_id = stripe_price.id
            product_plan.stripe_product_id = stripe_product_id
            product_plan.save(update_fields=['stripe_price_id', 'stripe_product_id'])

            logger.info(f"Synced product plan {product_plan.id} to Stripe: {stripe_price.id}")
            return stripe_price.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to sync product plan {product_plan.id} to Stripe: {str(e)}")
            raise

    # =================================================================
    # SUBSCRIPTION MANAGEMENT
    # =================================================================

    @transaction.atomic
    def create_subscription(
        self,
        organization: Organization,
        product_plan: ProductPlan,
        payment_method_id: Optional[str] = None,
        trial_days: Optional[int] = None
    ) -> ProductSubscription:
        """
        Create a new subscription in both Stripe and local database

        Args:
            organization: Organization subscribing
            product_plan: ProductPlan to subscribe to
            payment_method_id: Stripe payment method ID (optional for trial)
            trial_days: Number of trial days (optional)

        Returns:
            ProductSubscription: Created subscription instance
        """
        from django.utils import timezone
        from datetime import timedelta

        # Get or create Stripe customer
        customer_id = self.get_or_create_customer(organization)

        # Ensure product plan has Stripe price ID
        if not product_plan.stripe_price_id:
            self.sync_product_plan_to_stripe(product_plan)

        try:
            # Prepare subscription parameters
            subscription_params = {
                'customer': customer_id,
                'items': [{
                    'price': product_plan.stripe_price_id,
                }],
                'metadata': {
                    'organization_id': str(organization.id),
                    'product_id': str(product_plan.product.id),
                    'product_plan_id': str(product_plan.id)
                }
            }

            # Add payment method if provided
            if payment_method_id:
                subscription_params['default_payment_method'] = payment_method_id

            # Add trial period if specified
            if trial_days:
                subscription_params['trial_period_days'] = trial_days
            elif product_plan.base_plan.trial_period_days > 0:
                subscription_params['trial_period_days'] = product_plan.base_plan.trial_period_days

            # Create subscription in Stripe
            stripe_subscription = stripe.Subscription.create(**subscription_params)

            # Calculate period dates
            now = timezone.now()
            current_period_start = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_start,
                tz=timezone.get_current_timezone()
            )
            current_period_end = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_end,
                tz=timezone.get_current_timezone()
            )

            # Determine trial end date
            trial_end_date = None
            if stripe_subscription.trial_end:
                trial_end_date = timezone.datetime.fromtimestamp(
                    stripe_subscription.trial_end,
                    tz=timezone.get_current_timezone()
                )

            # Create local ProductSubscription
            product_subscription = ProductSubscription.objects.create(
                organization=organization,
                product=product_plan.product,
                plan=product_plan,
                status='trial' if stripe_subscription.status == 'trialing' else stripe_subscription.status,
                started_at=now,
                trial_end_date=trial_end_date,
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                next_billing_date=current_period_end,
                auto_renew=True,
                stripe_subscription_id=stripe_subscription.id,
                current_usage={},
                usage_limit=product_plan.product_limits or {},
                metadata={
                    'stripe_status': stripe_subscription.status,
                    'created_via': 'api'
                }
            )

            logger.info(
                f"Created subscription {product_subscription.id} "
                f"(Stripe: {stripe_subscription.id}) for {organization.name}"
            )

            return product_subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe subscription: {str(e)}")
            raise

    def cancel_subscription(
        self,
        product_subscription: ProductSubscription,
        at_period_end: bool = True,
        reason: str = None
    ) -> ProductSubscription:
        """
        Cancel a subscription in Stripe and update local database

        Args:
            product_subscription: ProductSubscription to cancel
            at_period_end: Whether to cancel at end of billing period
            reason: Cancellation reason

        Returns:
            ProductSubscription: Updated subscription
        """
        from django.utils import timezone

        if not product_subscription.stripe_subscription_id:
            raise ValueError("Subscription has no Stripe subscription ID")

        try:
            # Cancel in Stripe
            stripe_subscription = stripe.Subscription.modify(
                product_subscription.stripe_subscription_id,
                cancel_at_period_end=at_period_end,
                metadata={
                    'cancellation_reason': reason or 'User requested',
                    'cancelled_at': timezone.now().isoformat()
                }
            )

            # Update local subscription
            product_subscription.auto_renew = False
            if not at_period_end:
                product_subscription.status = 'cancelled'
                product_subscription.cancelled_at = timezone.now()
            product_subscription.cancellation_reason = reason or 'User requested cancellation'
            product_subscription.save()

            logger.info(
                f"Cancelled subscription {product_subscription.id} "
                f"(at_period_end={at_period_end})"
            )

            return product_subscription

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to cancel Stripe subscription "
                f"{product_subscription.stripe_subscription_id}: {str(e)}"
            )
            raise

    def reactivate_subscription(
        self,
        product_subscription: ProductSubscription
    ) -> ProductSubscription:
        """
        Reactivate a cancelled subscription

        Args:
            product_subscription: ProductSubscription to reactivate

        Returns:
            ProductSubscription: Updated subscription
        """
        if not product_subscription.stripe_subscription_id:
            raise ValueError("Subscription has no Stripe subscription ID")

        if product_subscription.status not in ['cancelled', 'past_due']:
            raise ValueError(f"Cannot reactivate subscription with status: {product_subscription.status}")

        try:
            # Reactivate in Stripe
            stripe_subscription = stripe.Subscription.modify(
                product_subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )

            # Update local subscription
            product_subscription.status = 'active'
            product_subscription.auto_renew = True
            product_subscription.cancelled_at = None
            product_subscription.cancellation_reason = ''
            product_subscription.save()

            logger.info(f"Reactivated subscription {product_subscription.id}")
            return product_subscription

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to reactivate Stripe subscription "
                f"{product_subscription.stripe_subscription_id}: {str(e)}"
            )
            raise

    # =================================================================
    # PAYMENT METHOD MANAGEMENT
    # =================================================================

    def attach_payment_method(
        self,
        organization: Organization,
        payment_method_id: str,
        set_as_default: bool = True
    ) -> PaymentMethod:
        """
        Attach a payment method to a customer

        Args:
            organization: Organization to attach payment method to
            payment_method_id: Stripe payment method ID
            set_as_default: Whether to set as default payment method

        Returns:
            PaymentMethod: Created local payment method record
        """
        customer_id = self.get_or_create_customer(organization)

        try:
            # Attach payment method to customer in Stripe
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )

            # Set as default if requested
            if set_as_default:
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method_id
                    }
                )

            # Get payment provider
            stripe_provider = PaymentProvider.objects.filter(
                provider_type='stripe',
                is_active=True
            ).first()

            if not stripe_provider:
                raise ValueError("Stripe payment provider not configured")

            # Create local PaymentMethod record
            local_payment_method = PaymentMethod.objects.create(
                organization=organization,
                provider=stripe_provider,
                payment_method_type=payment_method.type,
                last_four=payment_method.card.last4 if payment_method.type == 'card' else None,
                expiry_month=payment_method.card.exp_month if payment_method.type == 'card' else None,
                expiry_year=payment_method.card.exp_year if payment_method.type == 'card' else None,
                card_brand=payment_method.card.brand if payment_method.type == 'card' else None,
                is_default=set_as_default,
                is_active=True,
                stripe_payment_method_id=payment_method_id,
                metadata={
                    'stripe_customer_id': customer_id,
                    'billing_details': payment_method.billing_details
                }
            )

            logger.info(
                f"Attached payment method {payment_method_id} to "
                f"customer {customer_id}"
            )

            return local_payment_method

        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {str(e)}")
            raise

    # =================================================================
    # WEBHOOK HANDLING
    # =================================================================

    def construct_webhook_event(self, payload: bytes, sig_header: str):
        """
        Verify and construct webhook event from Stripe

        Args:
            payload: Raw request body
            sig_header: Stripe signature header

        Returns:
            stripe.Event: Verified webhook event
        """
        if not self.webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise

    def handle_webhook_event(self, event: Dict) -> bool:
        """
        Process Stripe webhook events

        Args:
            event: Stripe event dictionary

        Returns:
            bool: True if handled successfully
        """
        event_type = event['type']
        event_data = event['data']['object']

        logger.info(f"Processing Stripe webhook: {event_type}")

        handlers = {
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.payment_succeeded': self._handle_invoice_paid,
            'invoice.payment_failed': self._handle_invoice_payment_failed,
            'payment_method.attached': self._handle_payment_method_attached,
            'payment_method.detached': self._handle_payment_method_detached,
        }

        handler = handlers.get(event_type)
        if handler:
            try:
                handler(event_data)
                return True
            except Exception as e:
                logger.error(f"Error handling {event_type}: {str(e)}")
                raise
        else:
            logger.warning(f"Unhandled webhook event type: {event_type}")
            return False

    def _handle_subscription_created(self, subscription_data: Dict):
        """Handle subscription.created webhook"""
        # Subscription should already exist from create_subscription()
        # Just log for confirmation
        logger.info(f"Subscription created webhook: {subscription_data['id']}")

    def _handle_subscription_updated(self, subscription_data: Dict):
        """Handle subscription.updated webhook"""
        from django.utils import timezone

        stripe_subscription_id = subscription_data['id']

        try:
            subscription = ProductSubscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )

            # Update status
            status_map = {
                'active': 'active',
                'trialing': 'trial',
                'past_due': 'past_due',
                'canceled': 'cancelled',
                'unpaid': 'suspended'
            }
            subscription.status = status_map.get(
                subscription_data['status'],
                subscription_data['status']
            )

            # Update period dates
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription_data['current_period_start'],
                tz=timezone.get_current_timezone()
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription_data['current_period_end'],
                tz=timezone.get_current_timezone()
            )
            subscription.next_billing_date = subscription.current_period_end

            subscription.save()
            logger.info(f"Updated subscription {subscription.id} from webhook")

        except ProductSubscription.DoesNotExist:
            logger.warning(
                f"Subscription not found for Stripe ID: {stripe_subscription_id}"
            )

    def _handle_subscription_deleted(self, subscription_data: Dict):
        """Handle subscription.deleted webhook"""
        from django.utils import timezone

        stripe_subscription_id = subscription_data['id']

        try:
            subscription = ProductSubscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
            subscription.save()

            logger.info(f"Cancelled subscription {subscription.id} from webhook")

        except ProductSubscription.DoesNotExist:
            logger.warning(
                f"Subscription not found for Stripe ID: {stripe_subscription_id}"
            )

    def _handle_invoice_paid(self, invoice_data: Dict):
        """Handle invoice.payment_succeeded webhook"""
        # Create transaction record
        logger.info(f"Invoice paid: {invoice_data['id']}")
        # TODO: Create Invoice and Transaction records

    def _handle_invoice_payment_failed(self, invoice_data: Dict):
        """Handle invoice.payment_failed webhook"""
        logger.warning(f"Invoice payment failed: {invoice_data['id']}")
        # TODO: Handle failed payment (send notification, update subscription)

    def _handle_payment_method_attached(self, payment_method_data: Dict):
        """Handle payment_method.attached webhook"""
        logger.info(f"Payment method attached: {payment_method_data['id']}")

    def _handle_payment_method_detached(self, payment_method_data: Dict):
        """Handle payment_method.detached webhook"""
        logger.info(f"Payment method detached: {payment_method_data['id']}")
        # TODO: Update local PaymentMethod record
