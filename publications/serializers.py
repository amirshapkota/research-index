from rest_framework import serializers
from django.utils.text import slugify
from .models import (
    Publication, MeSHTerm, PublicationStats, 
    Citation, Reference, LinkOut, PublicationRead,
    Journal, EditorialBoardMember, JournalStats, Issue, IssueArticle,
    Topic, TopicBranch, JournalQuestionnaire
)
from users.models import Author, Institution


# ==================== TOPIC SERIALIZERS ====================

class TopicBranchListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing topic branches with hierarchy support."""
    publications_count = serializers.ReadOnlyField()
    children_count = serializers.ReadOnlyField()
    full_path = serializers.ReadOnlyField()
    parent_id = serializers.IntegerField(source='parent.id', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    
    class Meta:
        model = TopicBranch
        fields = [
            'id', 'name', 'slug', 'description', 'level',
            'parent_id', 'parent_name', 'full_path',
            'is_active', 'order', 'children_count', 'publications_count'
        ]
        read_only_fields = ['id', 'level']


class TopicBranchDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for topic branch with full hierarchy info and nested children."""
    topic_id = serializers.IntegerField(source='topic.id', read_only=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    parent_id = serializers.IntegerField(source='parent.id', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    full_path = serializers.ReadOnlyField()
    publications_count = serializers.ReadOnlyField()
    children_count = serializers.ReadOnlyField()
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = TopicBranch
        fields = [
            'id', 'topic_id', 'topic_name', 'parent_id', 'parent_name',
            'name', 'slug', 'description', 'level', 'full_path',
            'is_active', 'order', 'children_count', 'publications_count',
            'children', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'topic_id', 'topic_name', 'level', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        """Get immediate children branches."""
        children = obj.children.filter(is_active=True).order_by('order', 'name')
        return TopicBranchListSerializer(children, many=True, context=self.context).data


class TopicBranchCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating topic branches with hierarchy support."""
    
    slug = serializers.SlugField(required=False, allow_blank=True)
    
    class Meta:
        model = TopicBranch
        fields = [
            'id', 'topic', 'parent', 'name', 'slug', 'description', 
            'is_active', 'order'
        ]
        read_only_fields = ['id', 'level']
    
    def validate_slug(self, value):
        """Ensure slug is lowercase and URL-friendly."""
        if value:
            return value.lower().strip()
        return value
    
    def validate(self, data):
        """Validate hierarchy constraints and prevent duplicates at same level."""
        parent = data.get('parent')
        topic = data.get('topic', getattr(self.instance, 'topic', None))
        name = data.get('name')
        
        if parent:
            # Check depth limit
            if parent.level >= 4:
                raise serializers.ValidationError({
                    'parent': 'Maximum hierarchy depth is 4 levels. Cannot add child to level 4 branch.'
                })
            # Ensure parent belongs to same topic
            if topic and parent.topic != topic:
                raise serializers.ValidationError({
                    'parent': 'Parent branch must belong to the same topic.'
                })
        
        # Check for duplicate names at the same hierarchical level
        if name:
            from .models import TopicBranch
            query = TopicBranch.objects.filter(
                topic=topic,
                parent=parent,
                name__iexact=name  # Case-insensitive comparison
            )
            # Exclude current instance when updating
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                level_desc = f"under parent '{parent.name}'" if parent else "at the root level"
                raise serializers.ValidationError({
                    'name': f"A branch named '{name}' already exists {level_desc} in this topic. Please choose a different name."
                })
        
        return data
    
    def create(self, validated_data):
        """Auto-generate slug from name if not provided."""
        if not validated_data.get('slug'):
            validated_data['slug'] = slugify(validated_data['name'])
        try:
            return super().create(validated_data)
        except Exception as e:
            # Convert DB integrity errors into serializer validation errors
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                raise serializers.ValidationError({
                    "slug": ["A branch with this slug already exists for the given topic/parent."]
                })
            raise
    
    def update(self, instance, validated_data):
        """Auto-generate slug from name if not provided during update."""
        if 'slug' in validated_data and not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data.get('name', instance.name))
        try:
            return super().update(instance, validated_data)
        except Exception as e:
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                raise serializers.ValidationError({
                    "slug": ["A branch with this slug already exists for the given topic/parent."]
                })
            raise


class TopicListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing topics."""
    branches_count = serializers.ReadOnlyField()
    publications_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'is_active', 'order', 'branches_count', 
            'publications_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TopicDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for topic with hierarchical branch tree (only root-level branches)."""
    branches = serializers.SerializerMethodField()
    branches_count = serializers.ReadOnlyField()
    publications_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'is_active', 'order', 'branches', 'branches_count',
            'publications_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_branches(self, obj):
        """Get root-level branches (level 1) with their children recursively."""
        root_branches = obj.branches.filter(parent__isnull=True, is_active=True).order_by('order', 'name')
        return self._serialize_branch_tree(root_branches)
    
    def _serialize_branch_tree(self, branches):
        """Recursively serialize branch tree."""
        result = []
        for branch in branches:
            branch_data = {
                'id': branch.id,
                'name': branch.name,
                'slug': branch.slug,
                'description': branch.description,
                'level': branch.level,
                'full_path': branch.full_path,
                'is_active': branch.is_active,
                'order': branch.order,
                'publications_count': branch.publications_count,
                'children_count': branch.children_count,
            }
            # Add children recursively if they exist
            children = branch.children.filter(is_active=True).order_by('order', 'name')
            if children.exists():
                branch_data['children'] = self._serialize_branch_tree(children)
            else:
                branch_data['children'] = []
            result.append(branch_data)
        return result
    
    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'is_active', 'order', 'branches', 'branches_count',
            'publications_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TopicCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating topics."""
    
    slug = serializers.SlugField(required=False, allow_blank=True)
    
    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'is_active', 'order'
        ]
        read_only_fields = ['id']
    
    def validate_slug(self, value):
        """Ensure slug is lowercase and URL-friendly."""
        if value:
            return value.lower().strip()
        return value
    
    def validate_name(self, value):
        """Validate that topic name is unique (case-insensitive)."""
        query = Topic.objects.filter(name__iexact=value)
        # Exclude current instance when updating
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise serializers.ValidationError(
                f"A topic named '{value}' already exists. Please choose a different name."
            )
        return value
    
    def create(self, validated_data):
        """Auto-generate slug from name if not provided."""
        if not validated_data.get('slug'):
            validated_data['slug'] = slugify(validated_data['name'])
        try:
            return super().create(validated_data)
        except Exception as e:
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                raise serializers.ValidationError({
                    "name": ["A topic with this name already exists."]
                })
            raise
    
    def update(self, instance, validated_data):
        """Auto-generate slug from name if not provided during update."""
        if 'slug' in validated_data and not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data.get('name', instance.name))
        try:
            return super().update(instance, validated_data)
        except Exception as e:
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                raise serializers.ValidationError({
                    "name": ["A topic with this name already exists."]
                })
            raise


class TopicTreeSerializer(serializers.Serializer):
    """
    Serializer for topic tree structure.
    Returns topics with nested branches in a tree format suitable for frontend navigation.
    """
    
    def to_representation(self, instance):
        """
        Convert a queryset of topics into an array.
        Each topic contains its full branch tree.
        """
        result = []
        
        for topic in instance:
            # Build root-level branches with nested children
            root_branches = topic.branches.filter(parent__isnull=True, is_active=True).order_by('order', 'name')
            
            result.append({
                'id': topic.id,
                'name': topic.name,
                'slug': topic.slug,
                'description': topic.description,
                'icon': topic.icon,
                'branches': self._serialize_branch_tree(root_branches),
                'branches_count': topic.branches_count,
                'publications_count': topic.publications_count,
            })
        
        return result
    
    def _serialize_branch_tree(self, branches):
        """
        Recursively serialize branch tree with all nested children.
        """
        result = []
        
        for branch in branches:
            branch_data = {
                'id': branch.id,
                'name': branch.name,
                'slug': branch.slug,
                'description': branch.description,
                'level': branch.level,
                'full_path': branch.full_path,
                'children_count': branch.children_count,
                'publications_count': branch.publications_count,
            }
            
            # Add parent_id only if parent exists
            if branch.parent:
                branch_data['parent_id'] = branch.parent.id
            
            # Recursively add children
            children = branch.children.filter(is_active=True).order_by('order', 'name')
            if children.exists():
                branch_data['children'] = self._serialize_branch_tree(children)
            
            result.append(branch_data)
        
        return result


# ==================== MESH AND PUBLICATION SERIALIZERS ====================

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
    
    # Journal information
    journal_id = serializers.IntegerField(source='journal.id', read_only=True)
    journal_name = serializers.CharField(source='journal.title', read_only=True)
    journal_issn = serializers.CharField(source='journal.issn', read_only=True)
    
    # Issue information (from IssueArticle linkage)
    issue_id = serializers.SerializerMethodField()
    issue_number = serializers.SerializerMethodField()
    issue_volume = serializers.SerializerMethodField()
    
    # Topic information
    topic_branch_id = serializers.IntegerField(source='topic_branch.id', read_only=True, allow_null=True)
    topic_branch_name = serializers.CharField(source='topic_branch.name', read_only=True, allow_null=True)
    topic_id = serializers.IntegerField(source='topic_branch.topic.id', read_only=True, allow_null=True)
    topic_name = serializers.CharField(source='topic_branch.topic.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'author_name', 'author_orcid', 'publication_type',
            'publication_type_display', 'doi', 'published_date', 'journal_id',
            'journal_name', 'journal_issn', 'issue_id', 'issue_number', 'issue_volume',
            'abstract', 'pdf_url', 'is_published',
            'created_at', 'updated_at', 'stats', 'mesh_terms_count',
            'citations_count', 'references_count',
            'topic_branch_id', 'topic_branch_name', 'topic_id', 'topic_name'
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
    
    def get_issue_id(self, obj):
        """Get the issue ID if this publication is linked to an issue."""
        issue_article = obj.issue_appearances.first()
        return issue_article.issue.id if issue_article else None
    
    def get_issue_number(self, obj):
        """Get the issue number if this publication is linked to an issue."""
        issue_article = obj.issue_appearances.first()
        return issue_article.issue.issue_number if issue_article else None
    
    def get_issue_volume(self, obj):
        """Get the volume number if this publication is linked to an issue."""
        issue_article = obj.issue_appearances.first()
        return issue_article.issue.volume if issue_article else None


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
    
    # Topic information
    topic_branch = TopicBranchDetailSerializer(read_only=True)
    
    # Journal information
    journal_id = serializers.IntegerField(source='journal.id', read_only=True)
    journal_title = serializers.CharField(source='journal.title', read_only=True)
    journal_issn = serializers.CharField(source='journal.issn', read_only=True)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'abstract', 'publication_type', 'publication_type_display',
            'pdf_file', 'pdf_url', 'doi', 'published_date', 'journal', 'journal_id',
            'journal_title', 'journal_issn', 'volume', 'issue', 'pages', 'publisher',
            'co_authors', 'erratum_from', 'erratum_from_title',
            'pubmed_id', 'arxiv_id', 'pubmed_central_id',
            'topic_branch',
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
    
    issue_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="Issue ID to link this publication to"
    )
    
    class Meta:
        model = Publication
        fields = [
            'title', 'abstract', 'publication_type', 'pdf_file',
            'doi', 'published_date', 'journal', 'volume', 'issue',
            'pages', 'publisher', 'co_authors', 'erratum_from',
            'pubmed_id', 'arxiv_id', 'pubmed_central_id', 'is_published',
            'topic_branch',
            'mesh_terms_data', 'link_outs_data', 'issue_id'
        ]
    
    def create(self, validated_data):
        # Extract nested data
        mesh_terms_data = validated_data.pop('mesh_terms_data', [])
        link_outs_data = validated_data.pop('link_outs_data', [])
        issue_id = validated_data.pop('issue_id', None)
        
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
        
        # Link to issue if provided
        if issue_id:
            from publications.models import Issue, IssueArticle
            try:
                issue = Issue.objects.get(pk=issue_id)
                # Get the max order for this issue
                max_order = IssueArticle.objects.filter(issue=issue).count()
                IssueArticle.objects.create(
                    issue=issue,
                    publication=publication,
                    order=max_order + 1
                )
            except Issue.DoesNotExist:
                pass  # Silently ignore if issue doesn't exist
        
        return publication
    
    def update(self, instance, validated_data):
        # Extract nested data
        mesh_terms_data = validated_data.pop('mesh_terms_data', None)
        link_outs_data = validated_data.pop('link_outs_data', None)
        issue_id = validated_data.pop('issue_id', None)
        
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
        
        # Update issue linkage if provided
        if issue_id is not None:
            from publications.models import Issue, IssueArticle
            # Remove existing issue linkages
            instance.issue_appearances.all().delete()
            
            # Add new linkage if issue_id is provided
            if issue_id:
                try:
                    issue = Issue.objects.get(pk=issue_id)
                    # Get the max order for this issue
                    max_order = IssueArticle.objects.filter(issue=issue).count()
                    IssueArticle.objects.create(
                        issue=issue,
                        publication=instance,
                        order=max_order + 1
                    )
                except Issue.DoesNotExist:
                    pass  # Silently ignore if issue doesn't exist
        
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


class IssueArticleDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for articles in an issue with full publication info.
    """
    publication_id = serializers.IntegerField(source='publication.id', read_only=True)
    title = serializers.CharField(source='publication.title', read_only=True)
    authors = serializers.SerializerMethodField()
    abstract = serializers.CharField(source='publication.abstract', read_only=True)
    doi = serializers.CharField(source='publication.doi', read_only=True)
    pages = serializers.CharField(source='publication.pages', read_only=True)
    published_date = serializers.DateField(source='publication.published_date', read_only=True)
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = IssueArticle
        fields = [
            'id', 'publication_id', 'title', 'authors', 'abstract', 
            'doi', 'pages', 'published_date', 'pdf_url', 'order', 'section'
        ]
        read_only_fields = ['id']
    
    def get_authors(self, obj):
        """Get main author and co-authors."""
        main_author = obj.publication.author.full_name
        co_authors = obj.publication.co_authors
        
        if co_authors:
            return f"{main_author}, {co_authors}"
        return main_author
    
    def get_pdf_url(self, obj):
        """Get PDF URL if available."""
        if obj.publication.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.publication.pdf_file.url)
            return obj.publication.pdf_file.url
        return None


class IssueWithArticlesSerializer(serializers.ModelSerializer):
    """
    Issue serializer with nested articles for volume grouping.
    """
    articles = IssueArticleDetailSerializer(many=True, read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Issue
        fields = [
            'id', 'volume', 'issue_number', 'title', 'description',
            'cover_image_url', 'publication_date', 'is_special_issue',
            'articles'
        ]
    
    def get_cover_image_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


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
    
    def validate(self, attrs):
        """
        Validate that the combination of journal, volume, and issue_number is unique.
        """
        journal = self.context.get('journal')
        volume = attrs.get('volume')
        issue_number = attrs.get('issue_number')
        
        # Check for duplicates
        if self.instance:
            # Update case - exclude current instance from check
            existing = Issue.objects.filter(
                journal=journal,
                volume=volume,
                issue_number=issue_number
            ).exclude(pk=self.instance.pk).exists()
        else:
            # Create case - check if combination exists
            existing = Issue.objects.filter(
                journal=journal,
                volume=volume,
                issue_number=issue_number
            ).exists()
        
        if existing:
            raise serializers.ValidationError({
                'issue_number': f'An issue with Volume {volume}, Issue {issue_number} already exists for this journal.'
            })
        
        return attrs
    
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


# ==================== JOURNAL QUESTIONNAIRE SERIALIZERS ====================

class JournalQuestionnaireListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing questionnaires.
    """
    journal_title = serializers.CharField(source='journal.title', read_only=True)
    completeness_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = JournalQuestionnaire
        fields = [
            'id', 'journal', 'journal_title', 'is_complete', 
            'completeness_percentage', 'submission_date', 'last_updated'
        ]
        read_only_fields = ['id', 'submission_date', 'last_updated']
    
    def get_completeness_percentage(self, obj):
        return obj.calculate_completeness()


class JournalQuestionnaireDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for viewing complete questionnaire data.
    """
    journal_title = serializers.CharField(source='journal.title', read_only=True)
    journal_id = serializers.IntegerField(source='journal.id', read_only=True)
    completeness_percentage = serializers.SerializerMethodField()
    
    # Display choices
    publication_frequency_display = serializers.CharField(source='get_publication_frequency_display', read_only=True)
    publication_format_display = serializers.CharField(source='get_publication_format_display', read_only=True)
    peer_review_type_display = serializers.CharField(source='get_peer_review_type_display', read_only=True)
    oa_model_display = serializers.CharField(source='get_oa_model_display', read_only=True)
    license_type_display = serializers.CharField(source='get_license_type_display', read_only=True)
    digital_archiving_system_display = serializers.CharField(source='get_digital_archiving_system_display', read_only=True)
    
    class Meta:
        model = JournalQuestionnaire
        fields = '__all__'
        read_only_fields = ['id', 'journal', 'submission_date', 'last_updated']
    
    def get_completeness_percentage(self, obj):
        return obj.calculate_completeness()


class JournalQuestionnaireCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating journal questionnaires.
    """
    
    class Meta:
        model = JournalQuestionnaire
        exclude = ['id', 'submission_date', 'last_updated']
    
    def validate_foreign_board_members_percentage(self, value):
        """Validate percentage is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Percentage must be between 0 and 100.")
        return value
    
    def validate_average_acceptance_rate(self, value):
        """Validate acceptance rate is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Acceptance rate must be between 0 and 100.")
        return value
    
    def validate_foreign_authors_percentage(self, value):
        """Validate percentage is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Percentage must be between 0 and 100.")
        return value
    
    def validate_apc_amount(self, value):
        """Validate APC amount is non-negative if provided."""
        if value is not None and value < 0:
            raise serializers.ValidationError("APC amount must be non-negative.")
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        # If uses_peer_review is False, peer review fields should be cleared
        if not data.get('uses_peer_review', True):
            data['peer_review_type'] = ''
            data['reviewers_per_manuscript'] = None
            data['average_review_time_weeks'] = None
        
        # If has_apc is False, clear APC amount
        if not data.get('has_apc', False):
            data['apc_amount'] = None
            data['apc_currency'] = 'USD'
        
        # If not indexed in databases, clear indexing year
        if not data.get('indexed_databases', '').strip():
            data['year_first_indexed'] = None
        
        return data
    
    def create(self, validated_data):
        """Create questionnaire and link to journal."""
        journal = validated_data.get('journal')
        
        # Check if questionnaire already exists for this journal
        if JournalQuestionnaire.objects.filter(journal=journal).exists():
            raise serializers.ValidationError({
                'journal': 'A questionnaire already exists for this journal. Use update instead.'
            })
        
        questionnaire = JournalQuestionnaire.objects.create(**validated_data)
        
        # Update is_complete based on completeness
        if questionnaire.calculate_completeness() >= 90:
            questionnaire.is_complete = True
            questionnaire.save()
        
        return questionnaire
    
    def update(self, instance, validated_data):
        """Update questionnaire."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update is_complete based on completeness
        if instance.calculate_completeness() >= 90:
            instance.is_complete = True
        else:
            instance.is_complete = False
        
        instance.save()
        return instance

