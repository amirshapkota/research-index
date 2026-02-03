from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from .models import (
    SupportPage, Sponsor, PricingTier, SupportBenefit, WhySupportPoint,
    SponsorshipPartnershipContent, SponsorshipPoint, PartnershipPoint
)
from .serializers import (
    SupportPageSerializer, SponsorSerializer,
    PricingTierSerializer, SupportBenefitSerializer, WhySupportPointSerializer,
    SponsorshipPartnershipContentSerializer
)


class SupportPageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for support pages
    - Public: Read-only access (GET)
    - Admin: Full CRUD access
    """
    queryset = SupportPage.objects.all().prefetch_related(
        'pricing_tiers', 'benefits', 'why_support_points',
        'sponsorship_content__sponsorship_points',
        'sponsorship_content__partnership_points'
    )
    serializer_class = SupportPageSerializer
    lookup_field = 'page_type'

    def get_permissions(self):
        """
        Public can read, only admins can write
        """
        if self.action in ['list', 'retrieve', 'author_supporter', 'institutional_supporter', 'sponsorship_partnership']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        """Filter active pages for public, all for admins"""
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def author_supporter(self, request):
        """Get Author Supporter page content"""
        try:
            page = self.get_queryset().get(page_type='author_supporter')
            serializer = self.get_serializer(page)
            return Response(serializer.data)
        except SupportPage.DoesNotExist:
            return Response(
                {'error': 'Author Supporter page not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def institutional_supporter(self, request):
        """Get Institutional Supporter page content"""
        try:
            page = self.get_queryset().get(page_type='institutional_supporter')
            serializer = self.get_serializer(page)
            return Response(serializer.data)
        except SupportPage.DoesNotExist:
            return Response(
                {'error': 'Institutional Supporter page not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def sponsorship_partnership(self, request):
        """Get Sponsorship & Partnership page content"""
        try:
            page = self.get_queryset().get(page_type='sponsorship_partnership')
            serializer = self.get_serializer(page)
            return Response(serializer.data)
        except SupportPage.DoesNotExist:
            return Response(
                {'error': 'Sponsorship & Partnership page not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    # Nested resource actions for CRUD operations
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def pricing_tiers(self, request, page_type=None):
        """Create pricing tier for this page"""
        page = self.get_object()
        serializer = PricingTierSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(support_page=page)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def benefits(self, request, page_type=None):
        """Create benefit for this page"""
        page = self.get_object()
        serializer = SupportBenefitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(support_page=page)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def why_support(self, request, page_type=None):
        """Create why support point for this page"""
        page = self.get_object()
        serializer = WhySupportPointSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(support_page=page)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PricingTierViewSet(viewsets.ModelViewSet):
    """CRUD for pricing tiers"""
    queryset = PricingTier.objects.all()
    serializer_class = PricingTierSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class SupportBenefitViewSet(viewsets.ModelViewSet):
    """CRUD for support benefits"""
    queryset = SupportBenefit.objects.all()
    serializer_class = SupportBenefitSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class WhySupportPointViewSet(viewsets.ModelViewSet):
    """CRUD for why support points"""
    queryset = WhySupportPoint.objects.all()
    serializer_class = WhySupportPointSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class SponsorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for sponsors (public read, admin write)
    """
    queryset = Sponsor.objects.all()
    serializer_class = SponsorSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        """Filter active sponsors for public"""
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_active=True)

