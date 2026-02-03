from django.contrib import admin
from .models import (
    SupportPage, PricingTier, SupportBenefit, WhySupportPoint, Sponsor
)


class PricingTierInline(admin.TabularInline):
    model = PricingTier
    extra = 1
    fields = ['category', 'npr_amount', 'usd_amount', 'purpose', 'order']


class SupportBenefitInline(admin.TabularInline):
    model = SupportBenefit
    extra = 1
    fields = ['title', 'description', 'order']


class WhySupportPointInline(admin.TabularInline):
    model = WhySupportPoint
    extra = 1
    fields = ['title', 'description', 'order']


@admin.register(SupportPage)
class SupportPageAdmin(admin.ModelAdmin):
    list_display = ['page_type', 'title', 'is_active', 'updated_at']
    list_filter = ['page_type', 'is_active']
    search_fields = ['title', 'overview']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PricingTierInline, SupportBenefitInline, WhySupportPointInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('page_type', 'title', 'overview')
        }),
        ('Sponsorship & Partnership Details', {
            'fields': ('sponsorship_detail', 'partnership_detail'),
            'description': 'Only applicable for Sponsorship & Partnership page type'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order', 'show_on_author_supporter',
                    'show_on_institutional_supporter', 'show_on_sponsorship_partnership']
    list_filter = ['is_active', 'show_on_author_supporter',
                   'show_on_institutional_supporter', 'show_on_sponsorship_partnership']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'logo', 'website_url')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Show on Pages', {
            'fields': ('show_on_author_supporter', 'show_on_institutional_supporter',
                      'show_on_sponsorship_partnership')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


