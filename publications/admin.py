from django.contrib import admin
from .models import (
    Publication, MeSHTerm, PublicationStats,
    Citation, Reference, LinkOut, PublicationRead,
    Journal, EditorialBoardMember, JournalStats,
    Issue, IssueArticle,
    Topic, TopicBranch, JournalQuestionnaire
)


# ==================== TOPIC ADMIN ====================

class TopicBranchInline(admin.TabularInline):
    model = TopicBranch
    extra = 1
    fields = ['name', 'slug', 'is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order', 'branches_count', 'publications_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )
    
    inlines = [TopicBranchInline]
    
    def branches_count(self, obj):
        return obj.branches_count
    branches_count.short_description = 'Branches'
    
    def publications_count(self, obj):
        return obj.publications_count
    publications_count.short_description = 'Publications'


@admin.register(TopicBranch)
class TopicBranchAdmin(admin.ModelAdmin):
    list_display = ['indented_name', 'topic', 'level', 'parent', 'is_active', 'order', 'children_count', 'publications_count']
    list_filter = ['topic', 'level', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'description', 'topic__name', 'parent__name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['topic', 'level', 'order', 'name']
    raw_id_fields = ['parent']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('topic', 'parent', 'name', 'slug', 'description')
        }),
        ('Hierarchy', {
            'fields': ('level',),
            'classes': ('collapse',),
            'description': 'Level is auto-calculated based on parent'
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )
    
    readonly_fields = ['level']
    
    def indented_name(self, obj):
        """Display name with indentation based on hierarchy level."""
        indent = '—' * (obj.level - 1)
        return f"{indent} {obj.name}" if obj.level > 1 else obj.name
    indented_name.short_description = 'Name'
    
    def children_count(self, obj):
        return obj.children_count
    children_count.short_description = 'Children'
    
    def publications_count(self, obj):
        return obj.publications_count
    publications_count.short_description = 'Publications'


# ==================== PUBLICATION ADMIN ====================

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
        ('Classification', {
            'fields': ('topic_branch',)
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


# ==================== JOURNAL QUESTIONNAIRE ADMIN ====================

@admin.register(JournalQuestionnaire)
class JournalQuestionnaireAdmin(admin.ModelAdmin):
    list_display = [
        'journal', 
        'is_complete', 
        'completeness_percentage',
        'year_first_publication',
        'publisher_country',
        'submission_date',
        'last_updated'
    ]
    list_filter = [
        'is_complete',
        'publication_format',
        'publication_frequency',
        'uses_peer_review',
        'is_open_access',
        'assigns_dois',
        'submission_date'
    ]
    search_fields = [
        'journal__title',
        'journal_title',
        'publisher_name',
        'main_discipline',
        'editor_in_chief_name'
    ]
    readonly_fields = ['submission_date', 'last_updated', 'completeness_percentage']
    date_hierarchy = 'submission_date'
    
    fieldsets = (
        ('Journal Link', {
            'fields': ('journal',)
        }),
        ('Section 1: Journal Identity & Formal Data', {
            'fields': (
                'journal_title', 'issn', 'e_issn', 'publisher_name', 
                'publisher_country', 'year_first_publication', 'publication_frequency',
                'publication_format', 'journal_website_url', 'contact_email'
            )
        }),
        ('Section 2: Scientific Scope & Profile', {
            'fields': (
                'main_discipline', 'secondary_disciplines', 'aims_and_scope',
                'publishes_original_research', 'publishes_review_articles',
                'publishes_case_studies', 'publishes_short_communications', 'publishes_other'
            ),
            'classes': ('collapse',)
        }),
        ('Section 3: Editorial Board', {
            'fields': (
                'editor_in_chief_name', 'editor_in_chief_affiliation', 'editor_in_chief_country',
                'editorial_board_members_count', 'editorial_board_countries',
                'foreign_board_members_percentage', 'board_details_published'
            ),
            'classes': ('collapse',)
        }),
        ('Section 4: Peer Review Process', {
            'fields': (
                'uses_peer_review', 'peer_review_type', 'reviewers_per_manuscript',
                'average_review_time_weeks', 'reviewers_external',
                'peer_review_procedure_published', 'peer_review_procedure_url'
            ),
            'classes': ('collapse',)
        }),
        ('Section 5: Ethics & Publication Standards', {
            'fields': (
                'follows_publication_ethics', 'ethics_based_on_cope', 'ethics_based_on_icmje',
                'ethics_other_guidelines', 'uses_plagiarism_detection', 'plagiarism_software_name',
                'has_retraction_policy', 'retraction_policy_url',
                'has_conflict_of_interest_policy', 'conflict_of_interest_policy_url'
            ),
            'classes': ('collapse',)
        }),
        ('Section 6: Publishing Regularity & Stability', {
            'fields': (
                'issues_published_in_year', 'all_issues_published_on_time',
                'articles_published_in_year', 'submissions_rejected', 'average_acceptance_rate'
            ),
            'classes': ('collapse',)
        }),
        ('Section 7: Authors & Internationalization', {
            'fields': (
                'total_authors_in_year', 'foreign_authors_count', 'author_countries_count',
                'foreign_authors_percentage', 'encourages_international_submissions'
            ),
            'classes': ('collapse',)
        }),
        ('Section 8: Open Access & Fees', {
            'fields': (
                'is_open_access', 'oa_model', 'has_apc', 'apc_amount',
                'apc_currency', 'license_type'
            ),
            'classes': ('collapse',)
        }),
        ('Section 9: Digital Publishing Standards', {
            'fields': (
                'assigns_dois', 'doi_registration_agency', 'metadata_standards_used',
                'uses_online_submission_system', 'submission_system_name',
                'digital_archiving_system', 'other_archiving_system'
            ),
            'classes': ('collapse',)
        }),
        ('Section 10: Indexing & Visibility', {
            'fields': (
                'indexed_databases', 'year_first_indexed', 'indexed_in_google_scholar',
                'indexed_in_doaj', 'indexed_in_scopus', 'indexed_in_web_of_science',
                'abstracting_services'
            ),
            'classes': ('collapse',)
        }),
        ('Section 11: Website Quality & Transparency', {
            'fields': (
                'author_guidelines_available', 'peer_review_rules_available',
                'apcs_clearly_stated', 'journal_archive_accessible'
            ),
            'classes': ('collapse',)
        }),
        ('Section 12: Declarations & Verification', {
            'fields': (
                'data_is_verifiable', 'data_matches_website', 'consent_to_evaluation',
                'completed_by_name', 'completed_by_role', 'submission_date', 'last_updated'
            ),
            'classes': ('collapse',)
        }),
        ('Completion Status', {
            'fields': ('is_complete', 'completeness_percentage')
        }),
    )
    
    def completeness_percentage(self, obj):
        return f"{obj.calculate_completeness():.1f}%"
    completeness_percentage.short_description = 'Completeness'

