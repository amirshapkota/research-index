from django.contrib import admin
from .models import (
    Publication, MeSHTerm, PublicationStats,
    Citation, Reference, LinkOut, PublicationRead,
    Journal, EditorialBoardMember, JournalStats,
    Issue, IssueArticle
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


# ==================== JOURNAL ADMIN ====================

class EditorialBoardMemberInline(admin.TabularInline):
    model = EditorialBoardMember
    extra = 1
    fields = ['name', 'role', 'affiliation', 'email', 'orcid', 'order', 'is_active']
    ordering = ['order']


class IssueInline(admin.TabularInline):
    model = Issue
    extra = 0
    fields = ['volume', 'issue_number', 'title', 'publication_date', 'status']
    readonly_fields = ['created_at']


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ['title', 'institution', 'issn', 'frequency', 'is_open_access', 'peer_reviewed', 'is_active', 'created_at']
    list_filter = ['frequency', 'is_open_access', 'peer_reviewed', 'is_active', 'created_at']
    search_fields = ['title', 'short_title', 'issn', 'e_issn', 'institution__institution_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('institution', 'title', 'short_title', 'issn', 'e_issn', 'description', 'scope', 'cover_image')
        }),
        ('Publisher Information', {
            'fields': ('publisher_name', 'publisher_location', 'frequency', 'established_year')
        }),
        ('Information Sections', {
            'fields': ('about_journal', 'ethics_policies', 'writing_formatting', 'submitting_manuscript', 'help_support'),
            'classes': ('collapse',)
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address', 'website_url')
        }),
        ('Settings', {
            'fields': ('is_open_access', 'peer_reviewed', 'is_active', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [EditorialBoardMemberInline, IssueInline]


@admin.register(EditorialBoardMember)
class EditorialBoardMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'journal', 'role', 'affiliation', 'email', 'order', 'is_active']
    list_filter = ['role', 'is_active', 'journal']
    search_fields = ['name', 'affiliation', 'email', 'orcid', 'journal__title']
    ordering = ['journal', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('journal', 'name', 'role', 'affiliation', 'email')
        }),
        ('Professional Details', {
            'fields': ('title', 'bio', 'expertise', 'photo', 'orcid', 'google_scholar_profile')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active', 'joined_date', 'left_date')
        }),
    )


@admin.register(JournalStats)
class JournalStatsAdmin(admin.ModelAdmin):
    list_display = ['journal', 'impact_factor', 'cite_score', 'h_index', 'acceptance_rate', 'total_articles', 'total_issues', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['journal__title']
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('Impact Metrics', {
            'fields': ('impact_factor', 'cite_score', 'h_index', 'sjr_score')
        }),
        ('Editorial Metrics', {
            'fields': ('acceptance_rate', 'average_review_time')
        }),
        ('Content Metrics', {
            'fields': ('total_articles', 'total_issues', 'total_citations', 'total_reads')
        }),
        ('Engagement', {
            'fields': ('recommendations', 'last_updated')
        }),
    )


class IssueArticleInline(admin.TabularInline):
    model = IssueArticle
    extra = 0
    fields = ['publication', 'section', 'order']
    ordering = ['order']
    autocomplete_fields = ['publication']


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['get_issue_display', 'journal', 'publication_date', 'status', 'is_special_issue', 'created_at']
    list_filter = ['status', 'is_special_issue', 'publication_date', 'created_at']
    search_fields = ['title', 'volume', 'issue_number', 'journal__title', 'guest_editors']
    date_hierarchy = 'publication_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Issue Information', {
            'fields': ('journal', 'volume', 'issue_number', 'title', 'cover_image')
        }),
        ('Publication Details', {
            'fields': ('publication_date', 'submission_deadline', 'doi')
        }),
        ('Content', {
            'fields': ('editorial_note', 'guest_editors'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('status', 'is_special_issue', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [IssueArticleInline]
    
    def get_issue_display(self, obj):
        return f"Vol. {obj.volume}, Issue {obj.issue_number}"
    get_issue_display.short_description = 'Issue'


@admin.register(IssueArticle)
class IssueArticleAdmin(admin.ModelAdmin):
    list_display = ['publication', 'issue', 'section', 'order', 'added_at']
    list_filter = ['section', 'added_at']
    search_fields = ['publication__title', 'issue__title', 'section']
    date_hierarchy = 'added_at'
    readonly_fields = ['added_at']
    autocomplete_fields = ['publication', 'issue']
    ordering = ['issue', 'order']
