from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import (
    SupportPage, Sponsor, PricingTier, SupportBenefit, WhySupportPoint
)
from .serializers import (
    SupportPageSerializer, SponsorSerializer,
    PricingTierSerializer, SupportBenefitSerializer, WhySupportPointSerializer
)


# ==================== SUPPORT PAGE VIEWS ====================

class SupportPageListCreateView(generics.ListCreateAPIView):
    """
    List all support pages or create a new one.
    
    GET: Public access to active pages
    POST: Admin only
    """
    serializer_class = SupportPageSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        """Filter active pages for public, all for admins"""
        queryset = SupportPage.objects.all().prefetch_related(
            'pricing_tiers', 'benefits', 'why_support_points'
        )
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_active=True)
    
    @extend_schema(
        tags=['Support'],
        summary='List Support Pages',
        description='Retrieve all support pages (public sees active only).',
        responses={200: SupportPageSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Create Support Page',
        description='Create a new support page (admin only).',
        request=SupportPageSerializer,
        responses={
            201: SupportPageSerializer,
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SupportPageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a support page.
    """
    serializer_class = SupportPageSerializer
    lookup_field = 'page_type'
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        queryset = SupportPage.objects.all().prefetch_related(
            'pricing_tiers', 'benefits', 'why_support_points'
        )
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_active=True)
    
    @extend_schema(
        tags=['Support'],
        summary='Get Support Page',
        description='Retrieve a specific support page by page_type.',
        responses={
            200: SupportPageSerializer,
            404: OpenApiResponse(description='Page not found')
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Update Support Page',
        description='Update a support page (admin only).',
        request=SupportPageSerializer,
        responses={
            200: SupportPageSerializer,
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Delete Support Page',
        description='Delete a support page (admin only).',
        responses={
            204: OpenApiResponse(description='Page deleted'),
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AuthorSupporterPageView(APIView):
    """
    Get Author Supporter page content (public access).
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Support'],
        summary='Get Author Supporter Page',
        description='Retrieve the Author Supporter page content.',
        responses={
            200: SupportPageSerializer,
            404: OpenApiResponse(description='Page not found')
        }
    )
    def get(self, request):
        try:
            page = SupportPage.objects.prefetch_related(
                'pricing_tiers', 'benefits', 'why_support_points'
            ).get(page_type='author_supporter', is_active=True)
            serializer = SupportPageSerializer(page, context={'request': request})
            return Response(serializer.data)
        except SupportPage.DoesNotExist:
            return Response(
                {'error': 'Author Supporter page not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class InstitutionalSupporterPageView(APIView):
    """
    Get Institutional Supporter page content (public access).
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Support'],
        summary='Get Institutional Supporter Page',
        description='Retrieve the Institutional Supporter page content.',
        responses={
            200: SupportPageSerializer,
            404: OpenApiResponse(description='Page not found')
        }
    )
    def get(self, request):
        try:
            page = SupportPage.objects.prefetch_related(
                'pricing_tiers', 'benefits', 'why_support_points'
            ).get(page_type='institutional_supporter', is_active=True)
            serializer = SupportPageSerializer(page, context={'request': request})
            return Response(serializer.data)
        except SupportPage.DoesNotExist:
            return Response(
                {'error': 'Institutional Supporter page not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class SponsorshipPartnershipPageView(APIView):
    """
    Get Sponsorship & Partnership page content (public access).
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Support'],
        summary='Get Sponsorship & Partnership Page',
        description='Retrieve the Sponsorship & Partnership page content.',
        responses={
            200: SupportPageSerializer,
            404: OpenApiResponse(description='Page not found')
        }
    )
    def get(self, request):
        try:
            page = SupportPage.objects.prefetch_related(
                'pricing_tiers', 'benefits', 'why_support_points'
            ).get(page_type='sponsorship_partnership', is_active=True)
            
            serializer = SupportPageSerializer(page, context={'request': request})
            return Response(serializer.data)
        except SupportPage.DoesNotExist:
            return Response(
                {'error': 'Sponsorship & Partnership page not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==================== PRICING TIER VIEWS ====================

class PricingTierListCreateView(generics.ListCreateAPIView):
    """
    List all pricing tiers or create a new one.
    """
    queryset = PricingTier.objects.all().select_related('support_page')
    serializer_class = PricingTierSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    @extend_schema(
        tags=['Support'],
        summary='List Pricing Tiers',
        description='Retrieve all pricing tiers.',
        responses={200: PricingTierSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Create Pricing Tier',
        description='Create a new pricing tier (admin only).',
        request=PricingTierSerializer,
        responses={201: PricingTierSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PricingTierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a pricing tier.
    """
    queryset = PricingTier.objects.all().select_related('support_page')
    serializer_class = PricingTierSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    @extend_schema(
        tags=['Support'],
        summary='Get Pricing Tier',
        description='Retrieve a specific pricing tier.',
        responses={200: PricingTierSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Update Pricing Tier',
        description='Update a pricing tier (admin only).',
        request=PricingTierSerializer,
        responses={200: PricingTierSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Delete Pricing Tier',
        description='Delete a pricing tier (admin only).',
        responses={204: OpenApiResponse(description='Deleted')}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ==================== SUPPORT BENEFIT VIEWS ====================

class SupportBenefitListCreateView(generics.ListCreateAPIView):
    """
    List all support benefits or create a new one.
    """
    queryset = SupportBenefit.objects.all().select_related('support_page')
    serializer_class = SupportBenefitSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    @extend_schema(
        tags=['Support'],
        summary='List Support Benefits',
        description='Retrieve all support benefits.',
        responses={200: SupportBenefitSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Create Support Benefit',
        description='Create a new support benefit (admin only).',
        request=SupportBenefitSerializer,
        responses={201: SupportBenefitSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SupportBenefitDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a support benefit.
    """
    queryset = SupportBenefit.objects.all().select_related('support_page')
    serializer_class = SupportBenefitSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    @extend_schema(
        tags=['Support'],
        summary='Get Support Benefit',
        description='Retrieve a specific support benefit.',
        responses={200: SupportBenefitSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Update Support Benefit',
        description='Update a support benefit (admin only).',
        request=SupportBenefitSerializer,
        responses={200: SupportBenefitSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Delete Support Benefit',
        description='Delete a support benefit (admin only).',
        responses={204: OpenApiResponse(description='Deleted')}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ==================== WHY SUPPORT POINT VIEWS ====================

class WhySupportPointListCreateView(generics.ListCreateAPIView):
    """
    List all why support points or create a new one.
    """
    queryset = WhySupportPoint.objects.all().select_related('support_page')
    serializer_class = WhySupportPointSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    @extend_schema(
        tags=['Support'],
        summary='List Why Support Points',
        description='Retrieve all why support points.',
        responses={200: WhySupportPointSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Create Why Support Point',
        description='Create a new why support point (admin only).',
        request=WhySupportPointSerializer,
        responses={201: WhySupportPointSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class WhySupportPointDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a why support point.
    """
    queryset = WhySupportPoint.objects.all().select_related('support_page')
    serializer_class = WhySupportPointSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    @extend_schema(
        tags=['Support'],
        summary='Get Why Support Point',
        description='Retrieve a specific why support point.',
        responses={200: WhySupportPointSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Update Why Support Point',
        description='Update a why support point (admin only).',
        request=WhySupportPointSerializer,
        responses={200: WhySupportPointSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Delete Why Support Point',
        description='Delete a why support point (admin only).',
        responses={204: OpenApiResponse(description='Deleted')}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ==================== SPONSOR VIEWS ====================

class SponsorListCreateView(generics.ListCreateAPIView):
    """
    List all sponsors or create a new one.
    Public sees active only, admins see all.
    """
    serializer_class = SponsorSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        """Filter active sponsors for public"""
        queryset = Sponsor.objects.all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_active=True)
    
    @extend_schema(
        tags=['Support'],
        summary='List Sponsors',
        description='Retrieve all sponsors (public sees active only).',
        responses={200: SponsorSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Create Sponsor',
        description='Create a new sponsor (admin only).',
        request=SponsorSerializer,
        responses={201: SponsorSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SponsorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a sponsor.
    """
    serializer_class = SponsorSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        queryset = Sponsor.objects.all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_active=True)
    
    @extend_schema(
        tags=['Support'],
        summary='Get Sponsor',
        description='Retrieve a specific sponsor.',
        responses={200: SponsorSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Update Sponsor',
        description='Update a sponsor (admin only).',
        request=SponsorSerializer,
        responses={200: SponsorSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Support'],
        summary='Delete Sponsor',
        description='Delete a sponsor (admin only).',
        responses={204: OpenApiResponse(description='Deleted')}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

