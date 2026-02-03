from rest_framework import serializers
from .models import (
    SupportPage, PricingTier, SupportBenefit, WhySupportPoint,
    Sponsor
)


class PricingTierSerializer(serializers.ModelSerializer):
    support_page_title = serializers.CharField(source='support_page.title', read_only=True)
    
    class Meta:
        model = PricingTier
        fields = [
            'id', 'support_page', 'support_page_title', 'category', 
            'npr_amount', 'usd_amount', 'purpose', 'order'
        ]
        read_only_fields = ['id', 'support_page_title']
        extra_kwargs = {
            'support_page': {'required': False}  # Will be set by the view
        }


class SupportBenefitSerializer(serializers.ModelSerializer):
    support_page_title = serializers.CharField(source='support_page.title', read_only=True)
    
    class Meta:
        model = SupportBenefit
        fields = ['id', 'support_page', 'support_page_title', 'title', 'description', 'order']
        read_only_fields = ['id', 'support_page_title']
        extra_kwargs = {
            'support_page': {'required': False}
        }


class WhySupportPointSerializer(serializers.ModelSerializer):
    support_page_title = serializers.CharField(source='support_page.title', read_only=True)
    
    class Meta:
        model = WhySupportPoint
        fields = ['id', 'support_page', 'support_page_title', 'title', 'description', 'order']
        read_only_fields = ['id', 'support_page_title']
        extra_kwargs = {
            'support_page': {'required': False}
        }


class SponsorSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Sponsor
        fields = [
            'id', 'name', 'logo', 'logo_url', 'website_url', 
            'is_active', 'order',
            'show_on_author_supporter', 'show_on_institutional_supporter',
            'show_on_sponsorship_partnership',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'logo': {'write_only': True}  # Don't expose file path, use logo_url instead
        }
    
    def get_logo_url(self, obj):
        """Get full URL for logo image."""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class SupportPageSerializer(serializers.ModelSerializer):
    pricing_tiers = PricingTierSerializer(many=True, read_only=True)
    benefits = SupportBenefitSerializer(many=True, read_only=True)
    why_support_points = WhySupportPointSerializer(many=True, read_only=True)
    sponsors = serializers.SerializerMethodField()
    page_type_display = serializers.CharField(source='get_page_type_display', read_only=True)

    class Meta:
        model = SupportPage
        fields = [
            'id', 'page_type', 'page_type_display', 'title', 'overview', 
            'pricing_tiers', 'benefits', 'why_support_points', 'sponsors', 
            'sponsorship_detail', 'partnership_detail',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'page_type_display', 'created_at', 'updated_at']

    def get_sponsors(self, obj):
        # Filter sponsors based on page type
        if obj.page_type == 'author_supporter':
            sponsors = Sponsor.objects.filter(show_on_author_supporter=True, is_active=True)
        elif obj.page_type == 'institutional_supporter':
            sponsors = Sponsor.objects.filter(show_on_institutional_supporter=True, is_active=True)
        elif obj.page_type == 'sponsorship_partnership':
            sponsors = Sponsor.objects.filter(show_on_sponsorship_partnership=True, is_active=True)
        else:
            sponsors = Sponsor.objects.none()
        
        return SponsorSerializer(sponsors, many=True).data
