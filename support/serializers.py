from rest_framework import serializers
from .models import (
    SupportPage, PricingTier, SupportBenefit, WhySupportPoint,
    Sponsor, SponsorshipPartnershipContent, SponsorshipPoint, PartnershipPoint
)


class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingTier
        fields = ['id', 'category', 'npr_amount', 'usd_amount', 'purpose', 'order']


class SupportBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportBenefit
        fields = ['id', 'title', 'description', 'order']


class WhySupportPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhySupportPoint
        fields = ['id', 'title', 'description', 'order']


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsor
        fields = ['id', 'name', 'logo', 'website_url', 'order']


class SponsorshipPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorshipPoint
        fields = ['id', 'text', 'order']


class PartnershipPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnershipPoint
        fields = ['id', 'text', 'order']


class SponsorshipPartnershipContentSerializer(serializers.ModelSerializer):
    sponsorship_points = SponsorshipPointSerializer(many=True, read_only=True)
    partnership_points = PartnershipPointSerializer(many=True, read_only=True)

    class Meta:
        model = SponsorshipPartnershipContent
        fields = ['sponsorship_intro', 'partnership_intro', 'join_cta',
                  'sponsorship_points', 'partnership_points']


class SupportPageSerializer(serializers.ModelSerializer):
    pricing_tiers = PricingTierSerializer(many=True, read_only=True)
    benefits = SupportBenefitSerializer(many=True, read_only=True)
    why_support_points = WhySupportPointSerializer(many=True, read_only=True)
    sponsors = serializers.SerializerMethodField()
    sponsorship_content = SponsorshipPartnershipContentSerializer(read_only=True)

    class Meta:
        model = SupportPage
        fields = ['id', 'page_type', 'title', 'overview', 'pricing_tiers',
                  'benefits', 'why_support_points', 'sponsors', 'sponsorship_content',
                  'created_at', 'updated_at']

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
