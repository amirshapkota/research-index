from rest_framework import serializers
from .models import (
    Publication, MeSHTerm, PublicationStats, 
    Citation, Reference, LinkOut, PublicationRead,
    Journal, EditorialBoardMember, JournalStats, Issue, IssueArticle
)
from users.models import Author, Institution


class MeSHTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeSHTerm
        fields = ['id', 'term', 'term_type']
        read_only_fields = ['id']


class CitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Citation
        fields = [
            'id', 'citing_title', 'citing_authors', 'citing_doi',
            'citing_year', 'citing_journal', 'added_at'
        ]
        read_only_fields = ['id', 'added_at']


class ReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = [
            'id', 'reference_text', 'reference_title', 'reference_authors',
            'reference_doi', 'reference_year', 'reference_journal', 'order'
        ]
        read_only_fields = ['id']


class LinkOutSerializer(serializers.ModelSerializer):
    link_type_display = serializers.CharField(source='get_link_type_display', read_only=True)
    
    class Meta:
        model = LinkOut
        fields = ['id', 'link_type', 'link_type_display', 'url', 'description']
        read_only_fields = ['id']


class PublicationStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationStats
        fields = [
            'citations_count', 'reads_count', 'downloads_count',
            'recommendations_count', 'altmetric_score', 'field_citation_ratio',
            'last_updated'
        ]
        read_only_fields = ['last_updated']


class PublicationListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing publications.
    """
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_orcid = serializers.CharField(source='author.orcid', read_only=True)
    publication_type_display = serializers.CharField(source='get_publication_type_display', read_only=True)
    pdf_url = serializers.SerializerMethodField()
    stats = PublicationStatsSerializer(read_only=True)
    mesh_terms_count = serializers.SerializerMethodField()
    citations_count = serializers.SerializerMethodField()
    references_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'author_name', 'author_orcid', 'publication_type',
            'publication_type_display', 'doi', 'published_date', 'journal_name',
            'abstract', 'pdf_url', 'is_published', 'created_at', 'updated_at',
            'stats', 'mesh_terms_count', 'citations_count', 'references_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None
    
    def get_mesh_terms_count(self, obj):
        return obj.mesh_terms.count()
    
    def get_citations_count(self, obj):
        return obj.citations.count()
    
    def get_references_count(self, obj):
        return obj.references.count()


class PublicationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer with all nested data for publication details.
    """
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_email = serializers.EmailField(source='author.user.email', read_only=True)
    author_orcid = serializers.CharField(source='author.orcid', read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    
    publication_type_display = serializers.CharField(source='get_publication_type_display', read_only=True)
    pdf_url = serializers.SerializerMethodField()
    
    # Nested serializers
    mesh_terms = MeSHTermSerializer(many=True, read_only=True)
    citations = CitationSerializer(many=True, read_only=True)
    references = ReferenceSerializer(many=True, read_only=True)
    link_outs = LinkOutSerializer(many=True, read_only=True)
    stats = PublicationStatsSerializer(read_only=True)
    
    # Erratum info
    erratum_from_title = serializers.CharField(source='erratum_from.title', read_only=True, allow_null=True)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'abstract', 'publication_type', 'publication_type_display',
            'pdf_file', 'pdf_url', 'doi', 'published_date', 'journal_name',
            'volume', 'issue', 'pages', 'publisher', 'co_authors',
            'erratum_from', 'erratum_from_title',
            'pubmed_id', 'arxiv_id', 'pubmed_central_id',
            'is_published', 'created_at', 'updated_at',
            'author_id', 'author_name', 'author_email', 'author_orcid',
            'mesh_terms', 'citations', 'references', 'link_outs', 'stats'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None


class PublicationCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating publications.
    """
    mesh_terms_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of MeSH terms: [{'term': 'term_name', 'term_type': 'major/minor'}]"
    )
    
    link_outs_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of link outs: [{'link_type': 'type', 'url': 'url', 'description': 'desc'}]"
    )
    
    class Meta:
        model = Publication
        fields = [
            'title', 'abstract', 'publication_type', 'pdf_file',
            'doi', 'published_date', 'journal_name', 'volume', 'issue',
            'pages', 'publisher', 'co_authors', 'erratum_from',
            'pubmed_id', 'arxiv_id', 'pubmed_central_id', 'is_published',
            'mesh_terms_data', 'link_outs_data'
        ]
    
    def create(self, validated_data):
        # Extract nested data
        mesh_terms_data = validated_data.pop('mesh_terms_data', [])
        link_outs_data = validated_data.pop('link_outs_data', [])
        
        # Get author from request context
        request = self.context.get('request')
        author = Author.objects.get(user=request.user)
        
        # Create publication
        publication = Publication.objects.create(author=author, **validated_data)
        
        # Create PublicationStats
        PublicationStats.objects.create(publication=publication)
        
        # Create MeSH terms
        for mesh_data in mesh_terms_data:
            MeSHTerm.objects.create(publication=publication, **mesh_data)
        
        # Create link outs
        for link_data in link_outs_data:
            LinkOut.objects.create(publication=publication, **link_data)
        
        return publication
    
    def update(self, instance, validated_data):
        # Extract nested data
        mesh_terms_data = validated_data.pop('mesh_terms_data', None)
        link_outs_data = validated_data.pop('link_outs_data', None)
        
        # Update publication fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update MeSH terms if provided
        if mesh_terms_data is not None:
            instance.mesh_terms.all().delete()
            for mesh_data in mesh_terms_data:
                MeSHTerm.objects.create(publication=instance, **mesh_data)
        
        # Update link outs if provided
        if link_outs_data is not None:
            instance.link_outs.all().delete()
            for link_data in link_outs_data:
                LinkOut.objects.create(publication=instance, **link_data)
        
        return instance


class AddCitationSerializer(serializers.ModelSerializer):
    """
    Serializer for adding citations to a publication.
    """
    class Meta:
        model = Citation
        fields = [
            'citing_title', 'citing_authors', 'citing_doi',
            'citing_year', 'citing_journal'
        ]
    
    def create(self, validated_data):
        publication = self.context['publication']
        citation = Citation.objects.create(publication=publication, **validated_data)
        
        # Increment citation count in stats
        stats, created = PublicationStats.objects.get_or_create(publication=publication)
        stats.citations_count += 1
        stats.save()
        
        return citation


class AddReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for adding references to a publication.
    """
    class Meta:
        model = Reference
        fields = [
            'reference_text', 'reference_title', 'reference_authors',
            'reference_doi', 'reference_year', 'reference_journal', 'order'
        ]
    
    def create(self, validated_data):
        publication = self.context['publication']
        return Reference.objects.create(publication=publication, **validated_data)


class BulkReferencesSerializer(serializers.Serializer):
    """
    Serializer for adding multiple references at once.
    """
    references = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of references"
    )
    
    def create(self, validated_data):
        publication = self.context['publication']
        references_data = validated_data['references']
        
        references = []
        for ref_data in references_data:
            references.append(Reference(publication=publication, **ref_data))
        
        return Reference.objects.bulk_create(references)


# ==================== JOURNAL SERIALIZERS ====================

class EditorialBoardMemberSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EditorialBoardMember
        fields = [
            'id', 'name', 'role', 'role_display', 'title', 'affiliation',
            'email', 'bio', 'expertise', 'photo', 'photo_url', 'orcid',
            'website', 'order', 'is_active'
        ]
        read_only_fields = ['id']
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class JournalStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalStats
        fields = [
            'impact_factor', 'cite_score', 'h_index', 'acceptance_rate',
            'average_review_time', 'total_articles', 'total_issues',
            'total_citations', 'total_reads', 'recommendations',
            'social_media_score', 'last_updated'
        ]
        read_only_fields = ['last_updated']


class JournalListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing journals.
    """
    institution_name = serializers.CharField(source='institution.institution_name', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    stats = JournalStatsSerializer(read_only=True)
    editorial_board_count = serializers.SerializerMethodField()
    issues_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Journal
        fields = [
            'id', 'title', 'short_title', 'issn', 'e_issn', 'description',
            'institution_name', 'publisher_name', 'frequency', 'frequency_display',
            'established_year', 'is_open_access', 'peer_reviewed', 'is_active',
            'cover_image_url', 'stats', 'editorial_board_count', 'issues_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_cover_image_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
    
    def get_editorial_board_count(self, obj):
        return obj.editorial_board.filter(is_active=True).count()
    
    def get_issues_count(self, obj):
        return obj.issues.count()


class JournalDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer with all information sections and editorial board.
    """
    institution_name = serializers.CharField(source='institution.institution_name', read_only=True)
    institution_id = serializers.IntegerField(source='institution.id', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    
    # Nested data
    editorial_board = EditorialBoardMemberSerializer(many=True, read_only=True)
    stats = JournalStatsSerializer(read_only=True)
    
    class Meta:
        model = Journal
        fields = [
            'id', 'institution_id', 'institution_name', 'title', 'short_title',
            'issn', 'e_issn', 'description', 'scope', 'cover_image', 'cover_image_url',
            'publisher_name', 'frequency', 'frequency_display', 'established_year',
            'language', 'about_journal', 'ethics_policies', 'writing_formatting',
            'submitting_manuscript', 'help_support', 'contact_email', 'contact_phone',
            'contact_address', 'website', 'doi_prefix', 'is_active', 'is_open_access',
            'peer_reviewed', 'created_at', 'updated_at', 'editorial_board', 'stats'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_cover_image_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class JournalCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating journals.
    """
    editorial_board_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of editorial board members"
    )
    
    class Meta:
        model = Journal
        fields = [
            'title', 'short_title', 'issn', 'e_issn', 'description', 'scope',
            'cover_image', 'publisher_name', 'frequency', 'established_year',
            'language', 'about_journal', 'ethics_policies', 'writing_formatting',
            'submitting_manuscript', 'help_support', 'contact_email', 'contact_phone',
            'contact_address', 'website', 'doi_prefix', 'is_active', 'is_open_access',
            'peer_reviewed', 'editorial_board_data'
        ]
    
    def create(self, validated_data):
        editorial_board_data = validated_data.pop('editorial_board_data', [])
        
        # Get institution from request context
        request = self.context.get('request')
        institution = Institution.objects.get(user=request.user)
        
        # Create journal
        journal = Journal.objects.create(institution=institution, **validated_data)
        
        # Create JournalStats
        JournalStats.objects.create(journal=journal)
        
        # Create editorial board members
        for member_data in editorial_board_data:
            EditorialBoardMember.objects.create(journal=journal, **member_data)
        
        return journal
    
    def update(self, instance, validated_data):
        editorial_board_data = validated_data.pop('editorial_board_data', None)
        
        # Update journal fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update editorial board if provided
        if editorial_board_data is not None:
            instance.editorial_board.all().delete()
            for member_data in editorial_board_data:
                EditorialBoardMember.objects.create(journal=instance, **member_data)
        
        return instance


class IssueArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for articles in an issue.
    """
    article_title = serializers.CharField(source='publication.title', read_only=True)
    article_authors = serializers.CharField(source='publication.author.full_name', read_only=True)
    article_doi = serializers.CharField(source='publication.doi', read_only=True)
    
    class Meta:
        model = IssueArticle
        fields = ['id', 'publication', 'article_title', 'article_authors', 'article_doi', 'order', 'section']
        read_only_fields = ['id']


class IssueListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing issues.
    """
    journal_title = serializers.CharField(source='journal.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    articles_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Issue
        fields = [
            'id', 'journal_title', 'volume', 'issue_number', 'title',
            'description', 'cover_image_url', 'publication_date',
            'status', 'status_display', 'is_special_issue',
            'articles_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_cover_image_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
    
    def get_articles_count(self, obj):
        return obj.articles.count()


class IssueDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for issues with all articles.
    """
    journal_title = serializers.CharField(source='journal.title', read_only=True)
    journal_id = serializers.IntegerField(source='journal.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    
    # Nested articles
    articles = IssueArticleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Issue
        fields = [
            'id', 'journal_id', 'journal_title', 'volume', 'issue_number',
            'title', 'description', 'cover_image', 'cover_image_url',
            'publication_date', 'submission_deadline', 'doi', 'pages_range',
            'editorial_note', 'guest_editors', 'status', 'status_display',
            'is_special_issue', 'created_at', 'updated_at', 'articles'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_cover_image_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class IssueCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating issues.
    """
    class Meta:
        model = Issue
        fields = [
            'volume', 'issue_number', 'title', 'description', 'cover_image',
            'publication_date', 'submission_deadline', 'doi', 'pages_range',
            'editorial_note', 'guest_editors', 'status', 'is_special_issue'
        ]
    
    def create(self, validated_data):
        journal = self.context['journal']
        issue = Issue.objects.create(journal=journal, **validated_data)
        
        # Update journal stats
        stats, created = JournalStats.objects.get_or_create(journal=journal)
        stats.total_issues += 1
        stats.save()
        
        return issue


class AddArticleToIssueSerializer(serializers.Serializer):
    """
    Serializer for adding articles to an issue.
    """
    publication_id = serializers.IntegerField(required=True)
    order = serializers.IntegerField(default=0)
    section = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def create(self, validated_data):
        issue = self.context['issue']
        publication_id = validated_data.pop('publication_id')
        
        from .models import Publication
        publication = Publication.objects.get(id=publication_id)
        
        return IssueArticle.objects.create(
            issue=issue,
            publication=publication,
            **validated_data
        )
