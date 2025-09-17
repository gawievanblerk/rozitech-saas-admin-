"""
Views for tenant management
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django_tenants.utils import schema_context
from .models import Organization as Tenant, OrganizationUser as TenantUser
from .serializers import (
    TenantSerializer, TenantCreateSerializer, TenantUserSerializer
    # TenantInvitationSerializer, TenantInvitationCreateSerializer,
    # AcceptInvitationSerializer, TenantSwitchSerializer
)


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenants
    """
    queryset = Tenant.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TenantCreateSerializer
        return TenantSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Tenant.objects.all()
        
        # Return only tenants where user is a member
        return Tenant.objects.filter(
            tenant_users__user=user,
            tenant_users__is_active=True
        ).distinct()
    
    # @action(detail=True, methods=['post'])
    # def invite_user(self, request, pk=None):
    #     """Invite a user to join the tenant"""
    #     tenant = self.get_object()
    #     serializer = TenantInvitationCreateSerializer(
    #         data=request.data,
    #         context={'request': request}
    #     )
    #     
    #     if serializer.is_valid():
    #         serializer.save(tenant=tenant)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get all users for a tenant"""
        tenant = self.get_object()
        tenant_users = TenantUser.objects.filter(tenant=tenant, is_active=True)
        serializer = TenantUserSerializer(tenant_users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """Get usage statistics for a tenant"""
        tenant = self.get_object()
        
        stats = {
            'users': {
                'current': tenant.current_users_count,
                'limit': tenant.max_users,
                'percentage': (tenant.current_users_count / tenant.max_users) * 100 if tenant.max_users > 0 else 0
            },
            'storage': {
                'current_gb': tenant.storage_usage_gb,
                'limit_gb': tenant.max_storage_gb,
                'percentage': (tenant.storage_usage_gb / tenant.max_storage_gb) * 100 if tenant.max_storage_gb > 0 else 0
            },
            'api_calls': {
                'current_month': 0,  # This would be calculated from actual usage
                'limit': tenant.max_api_calls_per_month,
                'percentage': 0
            }
        }
        
        return Response(stats)


# class TenantInvitationViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet for managing tenant invitations
#     """
#     queryset = TenantInvitation.objects.all()
#     permission_classes = [permissions.IsAuthenticated]
#     
#     def get_serializer_class(self):
#         if self.action == 'create':
#             return TenantInvitationCreateSerializer
#         return TenantInvitationSerializer
#     
#     def get_queryset(self):
#         user = self.request.user
#         if user.is_superuser:
#             return TenantInvitation.objects.all()
#         
#         # Return only invitations for tenants where user has admin access
#         return TenantInvitation.objects.filter(
#             tenant__tenant_users__user=user,
#             tenant__tenant_users__role__in=['owner', 'admin'],
#             tenant__tenant_users__is_active=True
#         ).distinct()


class TenantSetupView(APIView):
    """
    Initial tenant setup for new organizations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = TenantCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            tenant = serializer.save()
            
            # Create tenant owner relationship
            TenantUser.objects.create(
                tenant=tenant,
                user=request.user,
                role='owner'
            )
            
            # Return full tenant data
            response_serializer = TenantSerializer(tenant)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentTenantView(APIView):
    """
    Get current tenant information for authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get current tenant from thread-local storage
        from core.middleware.tenant_context import get_current_tenant
        
        current_tenant = get_current_tenant()
        if not current_tenant:
            return Response(
                {'error': 'No current tenant found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's role in current tenant
        try:
            tenant_user = TenantUser.objects.get(
                tenant=current_tenant,
                user=request.user,
                is_active=True
            )
            role = tenant_user.role
            permissions = tenant_user.permissions
        except TenantUser.DoesNotExist:
            role = None
            permissions = []
        
        serializer = TenantSerializer(current_tenant)
        data = serializer.data
        data['user_role'] = role
        data['user_permissions'] = permissions
        
        return Response(data)


class SwitchTenantView(APIView):
    """
    Switch to a different tenant
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tenant_id):
        # Validate access to tenant
        try:
            tenant_user = TenantUser.objects.get(
                tenant_id=tenant_id,
                user=request.user,
                is_active=True
            )
        except TenantUser.DoesNotExist:
            return Response(
                {'error': 'You don\'t have access to this tenant'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Switch to tenant schema
        tenant = tenant_user.tenant
        
        # Update session or return tenant info for frontend to handle
        serializer = TenantSerializer(tenant)
        data = serializer.data
        data['user_role'] = tenant_user.role
        data['user_permissions'] = tenant_user.permissions
        
        return Response(data)


# class AcceptInvitationView(APIView):
#     """
#     Accept a tenant invitation
#     """
#     permission_classes = [permissions.IsAuthenticated]
#     
#     def post(self, request, token):
#         try:
#             invitation = TenantInvitation.objects.get(token=token)
#         except TenantInvitation.DoesNotExist:
#             return Response(
#                 {'error': 'Invalid invitation token'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         
#         if invitation.is_expired:
#             return Response(
#                 {'error': 'Invitation has expired'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         
#         if invitation.status != 'pending':
#             return Response(
#                 {'error': 'Invitation is no longer valid'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         
#         # Accept invitation
#         try:
#             tenant_user = invitation.accept(request.user)
#             serializer = TenantUserSerializer(tenant_user)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except ValueError as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )