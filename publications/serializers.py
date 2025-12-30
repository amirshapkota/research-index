from rest_framework import serializers
from .models import (
    Publication, MeSHTerm, PublicationStats, 
    Citation, Reference, LinkOut, PublicationRead
)
from users.models import Author


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
