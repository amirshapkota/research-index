from django.urls import path
from .views import (
    # Support Page views
    SupportPageListCreateView,
    SupportPageDetailView,
    AuthorSupporterPageView,
    InstitutionalSupporterPageView,
    SponsorshipPartnershipPageView,
    # Pricing Tier views
    PricingTierListCreateView,
    PricingTierDetailView,
    # Support Benefit views
    SupportBenefitListCreateView,
    SupportBenefitDetailView,
    # Why Support Point views
    WhySupportPointListCreateView,
    WhySupportPointDetailView,
    # Sponsor views
    SponsorListCreateView,
    SponsorDetailView,
)

urlpatterns = [
    # Support Pages
    path('pages/', SupportPageListCreateView.as_view(), name='support-page-list'),
    path('pages/<str:page_type>/', SupportPageDetailView.as_view(), name='support-page-detail'),
    
    # Quick access endpoints for specific pages
    path('author-supporter/', AuthorSupporterPageView.as_view(), name='author-supporter-page'),
    path('institutional-supporter/', InstitutionalSupporterPageView.as_view(), name='institutional-supporter-page'),
    path('sponsorship-partnership/', SponsorshipPartnershipPageView.as_view(), name='sponsorship-partnership-page'),
    
    # Pricing Tiers
    path('pricing-tiers/', PricingTierListCreateView.as_view(), name='pricing-tier-list'),
    path('pricing-tiers/<int:pk>/', PricingTierDetailView.as_view(), name='pricing-tier-detail'),
    
    # Support Benefits
    path('benefits/', SupportBenefitListCreateView.as_view(), name='support-benefit-list'),
    path('benefits/<int:pk>/', SupportBenefitDetailView.as_view(), name='support-benefit-detail'),
    
    # Why Support Points
    path('why-support/', WhySupportPointListCreateView.as_view(), name='why-support-point-list'),
    path('why-support/<int:pk>/', WhySupportPointDetailView.as_view(), name='why-support-point-detail'),
    
    # Sponsors
    path('sponsors/', SponsorListCreateView.as_view(), name='sponsor-list'),
    path('sponsors/<int:pk>/', SponsorDetailView.as_view(), name='sponsor-detail'),
]
