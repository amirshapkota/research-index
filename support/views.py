from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import SupportPage, Sponsor
from .serializers import SupportPageSerializer, SponsorSerializer


class SupportPageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for support pages (read-only public access)
    """
    queryset = SupportPage.objects.filter(is_active=True).prefetch_related(
        'pricing_tiers', 'benefits', 'why_support_points',
        'sponsorship_content__sponsorship_points',
        'sponsorship_content__partnership_points'
    )
    serializer_class = SupportPageSerializer
    permission_classes = [AllowAny]
    lookup_field = 'page_type'

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


class SponsorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for sponsors (read-only public access)
    """
    queryset = Sponsor.objects.filter(is_active=True)
    serializer_class = SponsorSerializer
    permission_classes = [AllowAny]

