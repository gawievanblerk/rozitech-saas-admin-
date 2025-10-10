"""
Serializers for authentication API endpoints
"""
from rest_framework import serializers


class UserDataSerializer(serializers.Serializer):
    """User data nested serializer"""
    id = serializers.CharField()
    username = serializers.CharField()
    email = serializers.EmailField()
    fullName = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    avatarUrl = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField()


class UserVerificationSerializer(serializers.Serializer):
    """
    Serializer for token verification response
    """
    success = serializers.BooleanField()
    user = UserDataSerializer()


class SubscriptionDataSerializer(serializers.Serializer):
    """Subscription data nested serializer"""
    id = serializers.CharField()
    status = serializers.CharField()


class OrganizationSettingsSerializer(serializers.Serializer):
    """Organization settings nested serializer"""
    timezone = serializers.CharField()
    locale = serializers.CharField()


class OrganizationDataSerializer(serializers.Serializer):
    """Organization data nested serializer"""
    id = serializers.CharField()
    name = serializers.CharField()
    subscription = SubscriptionDataSerializer(required=False, allow_null=True)
    settings = OrganizationSettingsSerializer()


class OrganizationDetailSerializer(serializers.Serializer):
    """
    Serializer for organization details response
    """
    success = serializers.BooleanField()
    organization = OrganizationDataSerializer()


class SubscriptionLimitsSerializer(serializers.Serializer):
    """Subscription limits nested serializer"""
    maxUsers = serializers.IntegerField()
    maxStorage = serializers.IntegerField()


class SubscriptionDetailSerializer(serializers.Serializer):
    """Detailed subscription data"""
    id = serializers.CharField()
    status = serializers.CharField()
    productCode = serializers.CharField()
    tier = serializers.CharField(required=False)
    expiresAt = serializers.CharField(required=False, allow_null=True)
    limits = SubscriptionLimitsSerializer(required=False)


class SubscriptionCheckSerializer(serializers.Serializer):
    """
    Serializer for subscription check response
    """
    success = serializers.BooleanField()
    hasActiveSubscription = serializers.BooleanField()
    subscription = SubscriptionDetailSerializer(required=False)
    message = serializers.CharField(required=False)