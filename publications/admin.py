from django.contrib import admin
from .models import (
    Publication, MeSHTerm, PublicationStats,
    Citation, Reference, LinkOut, PublicationRead
)


class MeSHTermInline(admin.TabularInline):
    model = MeSHTerm
    extra = 1


class CitationInline(admin.TabularInline):
    model = Citation
    extra = 0
    fields = ['citing_title', 'citing_authors', 'citing_year']


class ReferenceInline(admin.TabularInline):
    model = Reference
    extra = 0
    fields = ['order', 'reference_text', 'reference_title']
    ordering = ['order']


class LinkOutInline(admin.TabularInline):
    model = LinkOut
    extra = 1


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'publication_type', 'published_date', 'doi', 'is_published', 'created_at']
    list_filter = ['publication_type', 'is_published', 'published_date', 'created_at']
    search_fields = ['title', 'abstract', 'doi', 'author__full_name']
    date_hierarchy = 'published_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('author', 'title', 'abstract', 'publication_type', 'pdf_file')
        }),
        ('Publication Details', {
            'fields': ('doi', 'published_date', 'journal_name', 'volume', 'issue', 'pages', 'publisher', 'co_authors')
        }),
        ('External IDs', {
            'fields': ('pubmed_id', 'arxiv_id', 'pubmed_central_id'),
            'classes': ('collapse',)
        }),
        ('Erratum', {
            'fields': ('erratum_from',),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_published', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [MeSHTermInline, CitationInline, ReferenceInline, LinkOutInline]


@admin.register(PublicationStats)
class PublicationStatsAdmin(admin.ModelAdmin):
    list_display = ['publication', 'citations_count', 'reads_count', 'downloads_count', 'recommendations_count', 'altmetric_score', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['publication__title']
    readonly_fields = ['last_updated']


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ['citing_title', 'publication', 'citing_year', 'citing_journal', 'added_at']
    list_filter = ['citing_year', 'added_at']
    search_fields = ['citing_title', 'citing_authors', 'publication__title']
    date_hierarchy = 'added_at'


@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ['reference_title', 'publication', 'reference_year', 'order']
    list_filter = ['reference_year']
    search_fields = ['reference_title', 'reference_text', 'publication__title']
    ordering = ['publication', 'order']


@admin.register(LinkOut)
class LinkOutAdmin(admin.ModelAdmin):
    list_display = ['publication', 'link_type', 'url']
    list_filter = ['link_type']
    search_fields = ['publication__title', 'url']


@admin.register(PublicationRead)
class PublicationReadAdmin(admin.ModelAdmin):
    list_display = ['publication', 'reader_email', 'reader_ip', 'read_at']
    list_filter = ['read_at']
    search_fields = ['publication__title', 'reader_email']
    date_hierarchy = 'read_at'
    readonly_fields = ['read_at']
