from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupportPageViewSet, SponsorViewSet,
    PricingTierViewSet, SupportBenefitViewSet, WhySupportPointViewSet
)

router = DefaultRouter()
router.register(r'pages', SupportPageViewSet, basename='support-pages')
router.register(r'sponsors', SponsorViewSet, basename='sponsors')
router.register(r'pricing-tiers', PricingTierViewSet, basename='pricing-tiers')
router.register(r'benefits', SupportBenefitViewSet, basename='benefits')
router.register(r'why-support', WhySupportPointViewSet, basename='why-support')

urlpatterns = [
    path('', include(router.urls)),
]
