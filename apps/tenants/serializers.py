"""
Serializers for tenant management API
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Tenant, Domain, TenantUser, TenantInvitation


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary']


class TenantSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)
    current_users_count = serializers.ReadOnlyField()
    storage_usage_gb = serializers.ReadOnlyField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'schema_name', 'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state_province', 
            'postal_code', 'country', 'company_registration', 'tax_number',
            'industry', 'tier', 'status', 'is_active', 'max_users',
            'max_storage_gb', 'max_api_calls_per_month', 'created_at',
            'updated_at', 'trial_end_date', 'last_activity', 'domains',
            'current_users_count', 'storage_usage_gb'
        ]
        read_only_fields = ['id', 'schema_name', 'created_at', 'updated_at']


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new tenants"""
    primary_domain = serializers.CharField(write_only=True)
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'slug', 'email', 'phone', 'website', 'address_line1',
            'address_line2', 'city', 'state_province', 'postal_code',
            'country', 'company_registration', 'tax_number', 'industry',
            'tier', 'primary_domain'
        ]
    
    def create(self, validated_data):
        primary_domain = validated_data.pop('primary_domain')
        
        # Create tenant
        tenant = Tenant.objects.create(**validated_data)
        
        # Create primary domain
        Domain.objects.create(
            tenant=tenant,
            domain=primary_domain,
            is_primary=True
        )
        
        return tenant


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']


class TenantUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'tenant', 'tenant_name', 'user', 'role', 'is_active',
            'permissions', 'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenantInvitationSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = TenantInvitation
        fields = [
            'id', 'tenant', 'tenant_name', 'email', 'role', 'invited_by',
            'invited_by_name', 'status', 'created_at', 'expires_at',
            'accepted_at', 'is_expired'
        ]
        read_only_fields = ['id', 'token', 'status', 'created_at', 'accepted_at']


class TenantInvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tenant invitations"""
    
    class Meta:
        model = TenantInvitation
        fields = ['tenant', 'email', 'role']
    
    def create(self, validated_data):
        from django.utils import timezone
        from datetime import timedelta
        
        # Set invitation expiry (7 days from now)
        validated_data['expires_at'] = timezone.now() + timedelta(days=7)
        validated_data['invited_by'] = self.context['request'].user
        
        return super().create(validated_data)


class AcceptInvitationSerializer(serializers.Serializer):
    """Serializer for accepting tenant invitations"""
    token = serializers.UUIDField()
    
    def validate_token(self, value):
        try:
            invitation = TenantInvitation.objects.get(token=value)
            if invitation.is_expired:
                raise serializers.ValidationError("Invitation has expired")
            if invitation.status != 'pending':
                raise serializers.ValidationError("Invitation is no longer valid")
        except TenantInvitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token")
        
        return value


class TenantSwitchSerializer(serializers.Serializer):
    """Serializer for switching between tenants"""
    tenant_id = serializers.UUIDField()
    
    def validate_tenant_id(self, value):
        user = self.context['request'].user
        
        # Check if user has access to this tenant
        if not TenantUser.objects.filter(
            tenant_id=value,
            user=user,
            is_active=True
        ).exists():
            raise serializers.ValidationError("You don't have access to this tenant")
        
        return value