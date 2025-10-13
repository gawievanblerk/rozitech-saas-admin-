# Unified Billing & Subscription Management
## Multi-Product SaaS Platform

**Date:** October 13, 2025
**Project:** Rozitech SaaS Admin Platform
**Status:** Planning → Implementation

---

## Executive Summary

This document outlines the implementation plan for unified billing and subscription management across the Rozitech platform suite (AutoFlow AI, BuildEasy, TeamSpace).

**Key Goals:**
1. ✅ Single billing interface for all products
2. ✅ Support individual product subscriptions
3. ✅ Support platform bundles (2-3 products)
4. ✅ Unified invoice generation
5. ✅ Stripe integration for payments
6. ✅ Usage-based billing support
7. ✅ Multi-currency support (USD primary, ZAR)

---

## Current State Analysis

### Existing Models (Strong Foundation ✅)

**Subscriptions App:**
- ✅ `PricingPlan` - Flexible plan structure with features/limits
- ✅ `Subscription` - Organization subscriptions with status tracking
- ✅ `Invoice` - Comprehensive invoice model

**Payments App:**
- ✅ `PaymentProvider` - Multi-gateway support (Stripe, PayFast, PayPal)
- ✅ `PaymentMethod` - Stored payment methods
- ✅ `Transaction` - Payment tracking with fees
- ✅ `PaymentAttempt` - Retry tracking
- ✅ `Refund` - Refund management
- ✅ `PaymentWebhook` - Webhook event tracking

**Tenants App:**
- ✅ `Organization` - Multi-tenant structure with limits
- ✅ `OrganizationUser` - Role-based access
- ✅ `Domain` - Custom domain support

### Gaps to Address

**Missing for Multi-Product:**
1. ❌ Product catalog (AutoFlow, BuildEasy, TeamSpace)
2. ❌ Product-specific subscriptions (multiple per org)
3. ❌ Bundle/package definitions
4. ❌ Usage tracking per product
5. ❌ Product-specific feature flags

**Integration Needs:**
1. ⚠️ Stripe API integration (not yet implemented)
2. ⚠️ Subscription lifecycle management
3. ⚠️ Automated billing/invoicing
4. ⚠️ Webhook processing
5. ⚠️ Usage metering

---

## Architecture Design

### Multi-Product Subscription Model

```
┌─────────────────────────────────────────────────────────────┐
│                       ORGANIZATION                           │
│                     (billing entity)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴──────────────┬────────────────┐
         │                            │                │
         ▼                            ▼                ▼
┌────────────────┐          ┌────────────────┐  ┌────────────────┐
│  AutoFlow AI   │          │   BuildEasy    │  │   TeamSpace    │
│  Subscription  │          │  Subscription  │  │  Subscription  │
├────────────────┤          ├────────────────┤  ├────────────────┤
│ • Active       │          │ • Canceled     │  │ • Trial        │
│ • $49/month    │          │ • Was $64/mo   │  │ • 14 days left │
│ • 25K tasks    │          │                │  │ • 10 users     │
└────────────────┘          └────────────────┘  └────────────────┘
         │                            │                │
         └─────────────┬──────────────┴────────────────┘
                       ▼
              ┌────────────────┐
              │ UNIFIED INVOICE│
              ├────────────────┤
              │ AutoFlow: $49  │
              │ TeamSpace: $10 │
              │ (trial promo)  │
              ├────────────────┤
              │ Total:    $59  │
              └────────────────┘
```

### Bundle Pricing

```
INDIVIDUAL PRICES:
- AutoFlow AI:    $24-$99/month
- BuildEasy:      $32-$129/month
- TeamSpace:      $10-$32/user/month

BUNDLE DISCOUNTS:
┌──────────────────────────────────────────────┐
│ Starter Bundle (AutoFlow + TeamSpace)       │
│ Regular: $24 + $10/user = $34+             │
│ Bundle:  $30/month                          │
│ Savings: ~12%                                │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ Professional Bundle (All 3 Products)         │
│ Regular: $49 + $64 + $18/user = $131+       │
│ Bundle:  $135/month (10 users included)      │
│ Savings: ~24%                                │
└──────────────────────────────────────────────┘
```

---

## Database Schema Extensions

### New Models Required

#### 1. Product Model

```python
class Product(models.Model):
    """
    Platform products (AutoFlow, BuildEasy, TeamSpace)
    """
    id = UUID
    code = CharField(unique=True)  # 'autoflow', 'buildeasy', 'teamspace'
    name = CharField               # 'AutoFlow AI'
    description = TextField
    is_active = BooleanField

    # Product type
    billing_type = CharField       # 'fixed', 'per_user', 'usage_based'

    # Metadata
    features = JSONField           # Product-specific features
    metadata = JSONField

    created_at = DateTimeField
    updated_at = DateTimeField
```

#### 2. ProductPlan Model (extends PricingPlan)

```python
class ProductPlan(models.Model):
    """
    Product-specific pricing plans
    """
    id = UUID
    product = ForeignKey(Product)
    base_plan = ForeignKey(PricingPlan)  # References existing plan structure

    # Product-specific limits
    product_limits = JSONField      # e.g., tasks for AutoFlow, apps for BuildEasy

    # Visibility
    is_available_standalone = Boolean
    is_available_in_bundle = Boolean
```

#### 3. ProductSubscription Model

```python
class ProductSubscription(models.Model):
    """
    Individual product subscriptions within an organization
    """
    id = UUID
    organization = ForeignKey(Organization)
    product = ForeignKey(Product)
    plan = ForeignKey(ProductPlan)
    parent_subscription = ForeignKey(Subscription, null=True)  # If part of bundle

    # Status
    status = CharField              # active, trial, cancelled, etc.

    # Dates
    started_at = DateTimeField
    trial_end_date = DateTimeField(null=True)
    current_period_start = DateTimeField
    current_period_end = DateTimeField
    cancelled_at = DateTimeField(null=True)

    # Usage tracking
    current_usage = JSONField       # Product-specific usage metrics
    usage_limit = JSONField         # Product-specific limits

    # Metadata
    metadata = JSONField
```

#### 4. SubscriptionBundle Model

```python
class SubscriptionBundle(models.Model):
    """
    Pre-defined product bundles with discount pricing
    """
    id = UUID
    code = CharField(unique=True)   # 'starter_bundle', 'pro_bundle'
    name = CharField                # 'Professional Bundle'
    description = TextField

    # Pricing
    base_price = DecimalField       # Bundle price
    currency = CharField
    billing_interval = CharField

    # Discount
    discount_type = CharField       # 'percentage', 'fixed'
    discount_value = DecimalField

    # Products included
    included_products = ManyToManyField(Product, through='BundleProduct')

    is_active = BooleanField
```

#### 5. Usage Tracking Model

```python
class UsageRecord(models.Model):
    """
    Track usage for usage-based billing
    """
    id = UUID
    product_subscription = ForeignKey(ProductSubscription)

    # Usage details
    metric_name = CharField         # 'api_calls', 'storage_gb', 'tasks_executed'
    quantity = DecimalField
    unit_price = DecimalField(null=True)

    # Period
    period_start = DateTimeField
    period_end = DateTimeField

    # Billing
    is_billed = BooleanField
    invoice = ForeignKey(Invoice, null=True)

    timestamp = DateTimeField
    metadata = JSONField
```

---

## Implementation Phases

### Phase 1: Core Multi-Product Support (Week 1-2)

**Goal:** Enable multiple product subscriptions per organization

**Tasks:**
1. ✅ Create `Product` model and seed initial products
2. ✅ Create `ProductPlan` model linking products to pricing
3. ✅ Create `ProductSubscription` model
4. ✅ Update `Subscription` model to support bundles
5. ✅ Create database migrations
6. ✅ Add admin interface for product management

**Deliverables:**
- [ ] Product models implemented
- [ ] Database migrated
- [ ] Admin interface functional
- [ ] Basic tests passing

### Phase 2: Bundle & Package Support (Week 3)

**Goal:** Support bundled product offerings

**Tasks:**
1. ✅ Create `SubscriptionBundle` model
2. ✅ Create `BundleProduct` through model
3. ✅ Implement bundle pricing logic
4. ✅ Create bundle subscription creation service
5. ✅ Add bundle management to admin

**Deliverables:**
- [ ] Bundle models implemented
- [ ] Bundle pricing calculations working
- [ ] Bundle subscription creation API
- [ ] Tests for bundle logic

### Phase 3: Stripe Integration (Week 4-5)

**Goal:** Integrate Stripe for payment processing

**Tasks:**
1. ✅ Set up Stripe API client service
2. ✅ Implement customer creation/sync
3. ✅ Implement subscription creation in Stripe
4. ✅ Implement payment method management
5. ✅ Set up webhook endpoints
6. ✅ Implement webhook event processing
7. ✅ Add retry logic for failed payments

**Deliverables:**
- [ ] Stripe service class implemented
- [ ] Customer sync working
- [ ] Subscription creation via Stripe
- [ ] Webhooks processing correctly
- [ ] Payment failure handling

### Phase 4: Usage-Based Billing (Week 6)

**Goal:** Support usage metering and billing

**Tasks:**
1. ✅ Create `UsageRecord` model
2. ✅ Implement usage tracking API
3. ✅ Create usage aggregation service
4. ✅ Implement usage-based invoice generation
5. ✅ Add usage dashboards

**Deliverables:**
- [ ] Usage tracking functional
- [ ] Usage reports generated
- [ ] Usage-based billing working
- [ ] Usage dashboards live

### Phase 5: Billing Automation (Week 7)

**Goal:** Automate billing processes

**Tasks:**
1. ✅ Create billing cycle management service
2. ✅ Implement automatic invoice generation
3. ✅ Implement automatic payment processing
4. ✅ Set up retry logic for failed payments
5. ✅ Implement dunning management (payment reminders)
6. ✅ Add email notifications

**Deliverables:**
- [ ] Automated invoice generation
- [ ] Automatic payment processing
- [ ] Failed payment retry logic
- [ ] Email notifications working

### Phase 6: API & Frontend (Week 8)

**Goal:** Customer-facing subscription management

**Tasks:**
1. ✅ Create REST API endpoints
2. ✅ Implement subscription upgrade/downgrade
3. ✅ Implement payment method management UI
4. ✅ Create billing portal
5. ✅ Add invoice download/viewing
6. ✅ Add usage dashboards

**Deliverables:**
- [ ] REST API documented
- [ ] Subscription management UI
- [ ] Billing portal functional
- [ ] Usage dashboards live

---

## API Endpoints Design

### Subscription Management

```
GET    /api/billing/subscriptions/
POST   /api/billing/subscriptions/
GET    /api/billing/subscriptions/{id}/
PATCH  /api/billing/subscriptions/{id}/
DELETE /api/billing/subscriptions/{id}/

POST   /api/billing/subscriptions/{id}/upgrade/
POST   /api/billing/subscriptions/{id}/downgrade/
POST   /api/billing/subscriptions/{id}/cancel/
POST   /api/billing/subscriptions/{id}/reactivate/
```

### Products & Plans

```
GET    /api/billing/products/
GET    /api/billing/products/{code}/
GET    /api/billing/products/{code}/plans/
GET    /api/billing/bundles/
GET    /api/billing/bundles/{code}/
```

### Payment Methods

```
GET    /api/billing/payment-methods/
POST   /api/billing/payment-methods/
DELETE /api/billing/payment-methods/{id}/
POST   /api/billing/payment-methods/{id}/set-default/
```

### Invoices

```
GET    /api/billing/invoices/
GET    /api/billing/invoices/{id}/
GET    /api/billing/invoices/{id}/download/
POST   /api/billing/invoices/{id}/pay/
```

### Usage

```
GET    /api/billing/usage/
POST   /api/billing/usage/track/
GET    /api/billing/usage/summary/
```

---

## Stripe Integration Architecture

### Stripe Objects Mapping

```
Stripe Object          →  Our Model
─────────────────────────────────────────
stripe.Customer        →  Organization
stripe.Product         →  Product
stripe.Price           →  ProductPlan
stripe.Subscription    →  ProductSubscription
stripe.PaymentMethod   →  PaymentMethod
stripe.Invoice         →  Invoice
stripe.PaymentIntent   →  Transaction
```

### Webhook Events to Handle

**High Priority:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `payment_method.attached`
- `payment_method.detached`

**Medium Priority:**
- `invoice.created`
- `invoice.finalized`
- `charge.succeeded`
- `charge.failed`
- `charge.refunded`

**Low Priority:**
- `customer.updated`
- `payment_intent.succeeded`
- `payment_intent.payment_failed`

---

## Configuration

### Environment Variables

```bash
# Stripe
STRIPE_API_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_MODE=test  # or 'live'

# Billing
BILLING_CURRENCY=USD
BILLING_RETRY_ATTEMPTS=3
BILLING_RETRY_DELAY_DAYS=3
BILLING_GRACE_PERIOD_DAYS=7

# Products
AUTOFLOW_PRODUCT_CODE=autoflow
BUILDEASY_PRODUCT_CODE=buildeasy
TEAMSPACE_PRODUCT_CODE=teamspace
```

### Django Settings

```python
# Billing Configuration
BILLING = {
    'DEFAULT_CURRENCY': 'USD',
    'SUPPORTED_CURRENCIES': ['USD', 'ZAR'],
    'TAX_RATE': 0.0,  # Configurable per region
    'PAYMENT_RETRY_ATTEMPTS': 3,
    'GRACE_PERIOD_DAYS': 7,
    'TRIAL_PERIOD_DAYS': 14,
}

# Stripe Configuration
STRIPE = {
    'API_KEY': env('STRIPE_API_KEY'),
    'PUBLISHABLE_KEY': env('STRIPE_PUBLISHABLE_KEY'),
    'WEBHOOK_SECRET': env('STRIPE_WEBHOOK_SECRET'),
    'MODE': env('STRIPE_MODE', default='test'),
}
```

---

## Testing Strategy

### Unit Tests

**Models:**
- Product CRUD operations
- ProductSubscription lifecycle
- Bundle price calculations
- Usage tracking calculations
- Invoice generation logic

**Services:**
- Stripe API integration
- Subscription creation/cancellation
- Payment processing
- Webhook event handling
- Usage aggregation

### Integration Tests

- End-to-end subscription creation
- Payment flow with Stripe test mode
- Webhook processing
- Automated billing cycle
- Bundle subscription creation

### Test Coverage Goal: 80%+

---

## Security Considerations

**Payment Data:**
- ✅ Never store card numbers (use Stripe tokens)
- ✅ Never store CVV codes
- ✅ Encrypt API keys in database
- ✅ Use HTTPS for all API calls
- ✅ Implement webhook signature verification

**Access Control:**
- ✅ Only organization owners can manage billing
- ✅ Payment methods visible only to authorized users
- ✅ Audit log all billing changes
- ✅ Rate limit payment API endpoints

**PCI Compliance:**
- ✅ Use Stripe.js (no card data touches our servers)
- ✅ Implement 3D Secure (SCA) for European customers
- ✅ Regular security audits

---

## Success Metrics

**Technical:**
- API response time < 200ms (95th percentile)
- Webhook processing < 5 seconds
- Payment success rate > 95%
- Test coverage > 80%

**Business:**
- Subscription activation time < 2 minutes
- Payment retry success rate > 30%
- Bundle adoption rate > 20%
- Churn rate < 5% monthly

---

## Next Steps

1. **Review & Approval** - Team review of this plan
2. **Environment Setup** - Stripe test account, API keys
3. **Phase 1 Implementation** - Start with core models
4. **Iterative Development** - 2-week sprints
5. **Testing** - Comprehensive test suite
6. **Documentation** - API docs, user guides
7. **Deployment** - Staged rollout to production

---

**Document Status:** Draft
**Last Updated:** October 13, 2025
**Next Review:** After Phase 1 completion