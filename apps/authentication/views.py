"""
Authentication views for TeamSpace integration
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.http import Http404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from apps.tenants.models import Organization, OrganizationUser
from apps.subscriptions.models import Subscription
from apps.authentication.serializers import (
    UserVerificationSerializer,
    OrganizationDetailSerializer,
    SubscriptionCheckSerializer
)


class TokenVerificationView(APIView):
    """
    Verify JWT token and return user information

    Endpoint: GET /api/auth/verify
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Verify authentication token",
        description="Verifies the JWT token and returns user information for SSO integration",
        responses={
            200: OpenApiResponse(
                response=UserVerificationSerializer,
                description="Token is valid, returns user information"
            ),
            401: OpenApiResponse(description="Invalid or expired token")
        },
        tags=["Authentication"]
    )
    def get(self, request):
        """
        Verify token and return user information
        """
        try:
            user = request.user

            # Get user's default organization (first one they're a member of)
            org_membership = OrganizationUser.objects.filter(
                user=user,
                is_active=True
            ).select_related('organization').first()

            user_role = org_membership.role if org_membership else 'member'

            user_data = {
                'success': True,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'fullName': user.get_full_name() or user.username,
                    'name': user.get_full_name() or user.username,
                    'avatarUrl': '',  # Add avatar logic if needed
                    'role': user_role
                }
            }

            serializer = UserVerificationSerializer(user_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Invalid or expired token'
            }, status=status.HTTP_401_UNAUTHORIZED)


class OrganizationDetailView(APIView):
    """
    Retrieve organization information and verify user access

    Endpoint: GET /api/organizations/{organizationId}
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get organization details",
        description="Retrieves organization information and verifies user has access",
        parameters=[
            OpenApiParameter(
                name='organization_id',
                type=str,
                location=OpenApiParameter.PATH,
                description='Organization UUID'
            )
        ],
        responses={
            200: OpenApiResponse(
                response=OrganizationDetailSerializer,
                description="Organization details retrieved successfully"
            ),
            403: OpenApiResponse(description="User does not have access to this organization"),
            404: OpenApiResponse(description="Organization not found")
        },
        tags=["Organizations"]
    )
    def get(self, request, organization_id):
        """
        Get organization details if user has access
        """
        try:
            # Get organization
            organization = get_object_or_404(Organization, id=organization_id)

            # Check if user has access to this organization
            org_membership = OrganizationUser.objects.filter(
                organization=organization,
                user=request.user,
                is_active=True
            ).first()

            if not org_membership:
                return Response({
                    'success': False,
                    'error': 'User does not have access to this organization'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get subscription if exists
            subscription_data = {}
            try:
                subscription = Subscription.objects.get(organization=organization)
                subscription_data = {
                    'id': str(subscription.id),
                    'status': subscription.status
                }
            except Subscription.DoesNotExist:
                subscription_data = None

            org_data = {
                'success': True,
                'organization': {
                    'id': str(organization.id),
                    'name': organization.name,
                    'subscription': subscription_data,
                    'settings': {
                        'timezone': 'UTC',
                        'locale': 'en-US'
                    }
                }
            }

            serializer = OrganizationDetailSerializer(org_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except (Organization.DoesNotExist, ValueError, Http404):
            # ValueError is raised when the UUID format is invalid
            # Http404 is raised by get_object_or_404
            return Response({
                'success': False,
                'error': 'Organization not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubscriptionCheckView(APIView):
    """
    Check if organization has active subscription for a product

    Endpoint: GET /api/subscriptions/check?organizationId={id}&productCode={code}
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Check subscription status",
        description="Checks if an organization has an active subscription for a specific product",
        parameters=[
            OpenApiParameter(
                name='organizationId',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Organization UUID',
                required=True
            ),
            OpenApiParameter(
                name='productCode',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Product code (e.g., "teamspace")',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                response=SubscriptionCheckSerializer,
                description="Subscription check completed"
            ),
            400: OpenApiResponse(description="Missing required parameters"),
            403: OpenApiResponse(description="User does not have access to this organization")
        },
        tags=["Subscriptions"]
    )
    def get(self, request):
        """
        Check subscription status for organization and product
        """
        try:
            organization_id = request.query_params.get('organizationId')
            product_code = request.query_params.get('productCode')

            if not organization_id or not product_code:
                return Response({
                    'success': False,
                    'error': 'Missing required parameters: organizationId and productCode'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get organization
            organization = get_object_or_404(Organization, id=organization_id)

            # Verify user has access to this organization
            org_membership = OrganizationUser.objects.filter(
                organization=organization,
                user=request.user,
                is_active=True
            ).first()

            if not org_membership:
                return Response({
                    'success': False,
                    'error': 'User does not have access to this organization'
                }, status=status.HTTP_403_FORBIDDEN)

            # Check for active subscription
            try:
                subscription = Subscription.objects.get(organization=organization)

                # Check if subscription has matching product code
                # Note: You'll need to add product_code field to Subscription model
                subscription_product_code = getattr(subscription, 'product_code', None)

                # Check if subscription is active
                is_active = subscription.status == 'active'
                is_product_match = subscription_product_code == product_code if subscription_product_code else True

                if is_active and is_product_match:
                    # Active subscription
                    response_data = {
                        'success': True,
                        'hasActiveSubscription': True,
                        'subscription': {
                            'id': str(subscription.id),
                            'status': subscription.status,
                            'productCode': subscription_product_code or product_code,
                            'tier': organization.tier,
                            'expiresAt': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                            'limits': {
                                'maxUsers': organization.max_users,
                                'maxStorage': organization.max_storage_gb * 1024 * 1024 * 1024  # Convert to bytes
                            }
                        }
                    }
                elif subscription.status == 'expired':
                    # Expired subscription
                    response_data = {
                        'success': True,
                        'hasActiveSubscription': False,
                        'subscription': {
                            'id': str(subscription.id),
                            'status': subscription.status,
                            'productCode': subscription_product_code or product_code,
                            'expiresAt': subscription.current_period_end.isoformat() if subscription.current_period_end else None
                        },
                        'message': f'{product_code.title()} subscription has expired'
                    }
                else:
                    # Inactive subscription
                    response_data = {
                        'success': True,
                        'hasActiveSubscription': False,
                        'message': f'No active {product_code} subscription found'
                    }

            except Subscription.DoesNotExist:
                # No subscription found
                response_data = {
                    'success': True,
                    'hasActiveSubscription': False,
                    'message': f'No active {product_code} subscription found'
                }

            serializer = SubscriptionCheckSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Organization.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Organization not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
