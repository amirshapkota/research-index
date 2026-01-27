from rest_framework import generics, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import (
    Publication, MeSHTerm, PublicationStats, 
    Citation, Reference, LinkOut, PublicationRead,
    Journal, EditorialBoardMember, JournalStats, Issue, IssueArticle,
    Topic, TopicBranch, JournalQuestionnaire
)
from .serializers import (
    PublicationListSerializer, PublicationDetailSerializer,
    PublicationCreateUpdateSerializer, AddCitationSerializer,
    AddReferenceSerializer, BulkReferencesSerializer,
    MeSHTermSerializer, LinkOutSerializer, PublicationStatsSerializer,
    JournalListSerializer, JournalDetailSerializer, JournalCreateUpdateSerializer,
    EditorialBoardMemberSerializer, JournalStatsSerializer,
    IssueListSerializer, IssueDetailSerializer, IssueCreateUpdateSerializer,
    AddArticleToIssueSerializer,
    TopicListSerializer, TopicDetailSerializer, TopicCreateUpdateSerializer,
    TopicBranchListSerializer, TopicBranchDetailSerializer, TopicBranchCreateUpdateSerializer,
    TopicTreeSerializer,
    JournalQuestionnaireListSerializer, JournalQuestionnaireDetailSerializer,
    JournalQuestionnaireCreateUpdateSerializer
)
from users.models import Author, Institution


# ==================== TOPIC VIEWS ====================

class TopicListCreateView(generics.ListCreateAPIView):
    """
    List all topics or create a new topic (admin only).
    
    GET: List all active topics with branch counts
    POST: Create a new topic
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TopicCreateUpdateSerializer
        return TopicListSerializer
    
    def get_queryset(self):
        # Show only active topics by default, or all if admin
        queryset = Topic.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset.prefetch_related('branches')
    
    @extend_schema(
        tags=['Topics'],
        summary='List Topics',
        description='Retrieve all topics with branch and publication counts.',
        responses={200: TopicListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Topics'],
        summary='Create Topic',
        description='Create a new topic (admin only).',
        request=TopicCreateUpdateSerializer,
        responses={
            201: TopicDetailSerializer,
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def post(self, request, *args, **kwargs):
        # Check if user is staff/admin
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can create topics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic = serializer.save()
        
        response_serializer = TopicDetailSerializer(topic)
        return Response({
            'message': 'Topic created successfully',
            'topic': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class TopicDetailView(APIView):
    """
    Retrieve, update, or delete a specific topic.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Topics'],
        summary='Get Topic Details',
        description='Retrieve complete topic information including all branches.',
        responses={200: TopicDetailSerializer}
    )
    def get(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        serializer = TopicDetailSerializer(topic)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Topics'],
        summary='Update Topic',
        description='Update topic information (admin only).',
        request=TopicCreateUpdateSerializer,
        responses={200: TopicDetailSerializer}
    )
    def patch(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can update topics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        topic = get_object_or_404(Topic, pk=pk)
        serializer = TopicCreateUpdateSerializer(topic, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        topic = serializer.save()
        
        response_serializer = TopicDetailSerializer(topic)
        return Response({
            'message': 'Topic updated successfully',
            'topic': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Topics'],
        summary='Delete Topic',
        description='Delete a topic (admin only).',
        responses={200: OpenApiResponse(description='Topic deleted')}
    )
    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can delete topics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        topic = get_object_or_404(Topic, pk=pk)
        name = topic.name
        topic.delete()
        
        return Response({
            'message': f'Topic "{name}" has been deleted successfully'
        }, status=status.HTTP_200_OK)


class TopicTreeView(APIView):
    """
    Get all topics with their complete branch trees in a nested format.
    Returns an array of topics with their branch hierarchies.
    Supports search by topic name, branch name, or description.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Topics'],
        summary='Get Topic Tree',
        description='Retrieve all topics with their complete branch hierarchies in a tree structure. Supports search query parameter to filter topics and branches.',
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search term to filter topics and branches by name or description',
                required=False
            )
        ],
        responses={200: OpenApiResponse(
            description='Array of topics with their branch hierarchies',
            examples=[
                OpenApiExample(
                    'Topic Tree Response',
                    value=[
                        {
                            "id": 1,
                            "name": "Technology",
                            "slug": "technology",
                            "description": "Research in computing, algorithms, AI, and related fields",
                            "icon": ":computer:",
                            "branches": [
                                {
                                    "id": 1,
                                    "name": "Information Technology",
                                    "slug": "information-technology",
                                    "description": "IT infrastructure and systems",
                                    "level": 1,
                                    "full_path": "Technology > Information Technology",
                                    "children_count": 5,
                                    "publications_count": 145,
                                    "children": []
                                }
                            ],
                            "branches_count": 12,
                            "publications_count": 533
                        }
                    ],
                    response_only=True
                )
            ]
        )}
    )
    def get(self, request):
        # Get search parameter
        search_query = request.query_params.get('search', '').strip()
        
        # Get all active topics with prefetched branches
        topics = Topic.objects.filter(is_active=True).prefetch_related(
            'branches__children',
            'branches__parent'
        ).order_by('order', 'name')
        
        # Apply search filter if provided
        if search_query:
            topics = topics.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(branches__name__icontains=search_query) |
                Q(branches__description__icontains=search_query)
            ).distinct()
        
        serializer = TopicTreeSerializer(instance=topics)
        data = serializer.to_representation(topics)
        return Response(data, status=status.HTTP_200_OK)


class TopicBranchListCreateView(generics.ListCreateAPIView):
    """
    List all branches for a topic or create a new branch.
    Supports hierarchical structure - can filter by parent or show all.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TopicBranchCreateUpdateSerializer
        return TopicBranchListSerializer
    
    def get_queryset(self):
        topic_pk = self.kwargs.get('topic_pk')
        parent_pk = self.request.query_params.get('parent')
        
        queryset = TopicBranch.objects.filter(topic_id=topic_pk)
        
        # Filter by parent if specified, otherwise show root-level branches
        if parent_pk:
            queryset = queryset.filter(parent_id=parent_pk)
        elif self.request.method == 'GET':
            # By default, only show root-level branches (no parent)
            queryset = queryset.filter(parent__isnull=True)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset.select_related('topic', 'parent').prefetch_related('children')
    
    @extend_schema(
        tags=['Topics'],
        summary='List Topic Branches',
        description='Retrieve branches for a specific topic. Use ?parent=<id> to get children of a specific branch.',
        parameters=[
            OpenApiParameter(
                name='parent',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Filter by parent branch ID. Omit to get root-level branches.',
                required=False
            )
        ],
        responses={200: TopicBranchListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Topics'],
        summary='Create Topic Branch',
        description='Create a new branch under a topic (admin only). Can specify parent for nested hierarchy (max 4 levels).',
        request=TopicBranchCreateUpdateSerializer,
        responses={201: TopicBranchDetailSerializer}
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can create topic branches'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        topic_pk = self.kwargs.get('topic_pk')
        topic = get_object_or_404(Topic, pk=topic_pk)
        
        # Set topic from URL if not provided in data
        data = request.data.copy()
        if 'topic' not in data:
            data['topic'] = topic.id
        # Ensure slug key exists so serializers with allow_blank=True accept blank slug
        # and let the serializer's create() auto-generate it when empty.
        if 'slug' not in data:
            data['slug'] = ''
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        
        response_serializer = TopicBranchDetailSerializer(branch)
        return Response({
            'message': 'Topic branch created successfully',
            'branch': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class TopicBranchDetailView(APIView):
    """
    Retrieve, update, or delete a specific topic branch.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Topics'],
        summary='Get Branch Details',
        description='Retrieve complete information about a topic branch.',
        responses={200: TopicBranchDetailSerializer}
    )
    def get(self, request, topic_pk, pk):
        branch = get_object_or_404(TopicBranch, pk=pk, topic_id=topic_pk)
        serializer = TopicBranchDetailSerializer(branch)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Topics'],
        summary='Update Branch',
        description='Update topic branch information (admin only).',
        request=TopicBranchCreateUpdateSerializer,
        responses={200: TopicBranchDetailSerializer}
    )
    def patch(self, request, topic_pk, pk):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can update topic branches'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        branch = get_object_or_404(TopicBranch, pk=pk, topic_id=topic_pk)
        serializer = TopicBranchCreateUpdateSerializer(branch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        
        response_serializer = TopicBranchDetailSerializer(branch)
        return Response({
            'message': 'Topic branch updated successfully',
            'branch': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Topics'],
        summary='Delete Branch',
        description='Delete a topic branch (admin only).',
        responses={200: OpenApiResponse(description='Branch deleted')}
    )
    def delete(self, request, topic_pk, pk):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can delete topic branches'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        branch = get_object_or_404(TopicBranch, pk=pk, topic_id=topic_pk)
        name = branch.name
        branch.delete()
        
        return Response({
            'message': f'Topic branch "{name}" has been deleted successfully'
        }, status=status.HTTP_200_OK)


class PublicationsByTopicBranchView(generics.ListAPIView):
    """
    List all publications under a specific topic branch.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicationListSerializer
    
    def get_queryset(self):
        topic_pk = self.kwargs.get('topic_pk')
        branch_pk = self.kwargs.get('branch_pk')
        
        return Publication.objects.filter(
            topic_branch_id=branch_pk,
            topic_branch__topic_id=topic_pk,
            is_published=True
        ).select_related(
            'author', 'stats', 'topic_branch', 'topic_branch__topic'
        ).prefetch_related('mesh_terms')
    
    @extend_schema(
        tags=['Topics'],
        summary='List Publications by Topic Branch',
        description='Retrieve all published publications under a specific topic branch.',
        responses={200: PublicationListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ==================== PUBLICATION VIEWS ====================

class PublicationListCreateView(generics.ListCreateAPIView):
    """
    List all publications for the authenticated author or create a new publication.
    
    GET: List all publications of the authenticated author
    POST: Create a new publication with PDF upload support
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PublicationCreateUpdateSerializer
        return PublicationListSerializer
    
    def get_queryset(self):
        # Get publications for the authenticated author
        try:
            author = Author.objects.get(user=self.request.user)
            return Publication.objects.filter(author=author).select_related(
                'author', 'stats', 'erratum_from'
            ).prefetch_related('mesh_terms', 'citations', 'references', 'link_outs')
        except Author.DoesNotExist:
            return Publication.objects.none()
    
    @extend_schema(
        tags=['Publications'],
        summary='List My Publications',
        description='Retrieve all publications for the authenticated author.',
        responses={
            200: PublicationListSerializer(many=True),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Publications'],
        summary='Create Publication',
        description='Create a new publication. Supports PDF upload and nested data for MeSH terms and link outs.',
        request=PublicationCreateUpdateSerializer,
        examples=[
            OpenApiExample(
                'Create Publication Example',
                value={
                    'title': 'Deep Learning Applications in Medical Imaging',
                    'abstract': 'This paper explores the use of deep learning...',
                    'publication_type': 'journal_article',
                    'doi': '10.1234/example.2024.001',
                    'published_date': '2024-01-15',
                    'journal_name': 'Journal of Medical AI',
                    'volume': '10',
                    'issue': '2',
                    'pages': '123-145',
                    'publisher': 'Medical Press',
                    'co_authors': 'Jane Smith, John Doe, Alice Johnson',
                    'pubmed_id': '12345678',
                    'is_published': True,
                    'mesh_terms_data': [
                        {'term': 'Deep Learning', 'term_type': 'major'},
                        {'term': 'Medical Imaging', 'term_type': 'major'},
                        {'term': 'Artificial Intelligence', 'term_type': 'minor'}
                    ],
                    'link_outs_data': [
                        {'link_type': 'pubmed', 'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/'},
                        {'link_type': 'doi', 'url': 'https://doi.org/10.1234/example.2024.001'}
                    ]
                },
                request_only=True,
            )
        ],
        responses={
            201: PublicationDetailSerializer,
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        publication = serializer.save()
        
        # Return detailed response
        response_serializer = PublicationDetailSerializer(publication, context={'request': request})
        return Response({
            'message': 'Publication created successfully',
            'publication': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class PublicationDetailView(APIView):
    """
    Retrieve, update, or delete a specific publication.
    
    GET: Get publication details
    PUT/PATCH: Update publication
    DELETE: Delete publication
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_object(self, pk, user):
        try:
            author = Author.objects.get(user=user)
            return get_object_or_404(
                Publication.objects.select_related('author', 'stats', 'erratum_from')
                .prefetch_related('mesh_terms', 'citations', 'references', 'link_outs'),
                pk=pk,
                author=author
            )
        except Author.DoesNotExist:
            return None
    
    @extend_schema(
        tags=['Publications'],
        summary='Get Publication Details',
        description='Retrieve detailed information about a specific publication including stats, citations, references, and MeSH terms.',
        responses={
            200: PublicationDetailSerializer,
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def get(self, request, pk):
        publication = self.get_object(pk, request.user)
        if not publication:
            return Response({'error': 'Publication not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PublicationDetailSerializer(publication, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Publications'],
        summary='Update Publication (Full)',
        description='Update all fields of a publication.',
        request=PublicationCreateUpdateSerializer,
        responses={
            200: PublicationDetailSerializer,
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def put(self, request, pk):
        publication = self.get_object(pk, request.user)
        if not publication:
            return Response({'error': 'Publication not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PublicationCreateUpdateSerializer(
            publication, 
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        publication = serializer.save()
        
        response_serializer = PublicationDetailSerializer(publication, context={'request': request})
        return Response({
            'message': 'Publication updated successfully',
            'publication': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Publications'],
        summary='Update Publication (Partial)',
        description='Partially update a publication.',
        request=PublicationCreateUpdateSerializer,
        responses={
            200: PublicationDetailSerializer,
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def patch(self, request, pk):
        publication = self.get_object(pk, request.user)
        if not publication:
            return Response({'error': 'Publication not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PublicationCreateUpdateSerializer(
            publication, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        publication = serializer.save()
        
        response_serializer = PublicationDetailSerializer(publication, context={'request': request})
        return Response({
            'message': 'Publication updated successfully',
            'publication': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Publications'],
        summary='Delete Publication',
        description='Permanently delete a publication and all associated data.',
        responses={
            200: OpenApiResponse(description='Publication deleted'),
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def delete(self, request, pk):
        publication = self.get_object(pk, request.user)
        if not publication:
            return Response({'error': 'Publication not found'}, status=status.HTTP_404_NOT_FOUND)
        
        title = publication.title
        publication.delete()
        
        return Response({
            'message': f'Publication "{title}" has been deleted successfully'
        }, status=status.HTTP_200_OK)


class PublicationStatsView(APIView):
    """
    Get or update statistics for a publication.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Publications'],
        summary='Get Publication Stats',
        description='Retrieve statistics for a publication including citations, reads, downloads, and altmetric score.',
        responses={
            200: PublicationStatsSerializer,
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def get(self, request, pk):
        try:
            author = Author.objects.get(user=request.user)
            publication = get_object_or_404(Publication, pk=pk, author=author)
            stats, created = PublicationStats.objects.get_or_create(publication=publication)
            
            serializer = PublicationStatsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Author.DoesNotExist:
            return Response({'error': 'Author profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        tags=['Publications'],
        summary='Update Publication Stats',
        description='Update statistics for a publication (admin/owner only).',
        request=PublicationStatsSerializer,
        responses={
            200: PublicationStatsSerializer,
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def patch(self, request, pk):
        try:
            author = Author.objects.get(user=request.user)
            publication = get_object_or_404(Publication, pk=pk, author=author)
            stats, created = PublicationStats.objects.get_or_create(publication=publication)
            
            serializer = PublicationStatsSerializer(stats, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'message': 'Stats updated successfully',
                'stats': serializer.data
            }, status=status.HTTP_200_OK)
        except Author.DoesNotExist:
            return Response({'error': 'Author profile not found'}, status=status.HTTP_404_NOT_FOUND)


class AddCitationView(APIView):
    """
    Add a citation to a publication.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Publications'],
        summary='Add Citation',
        description='Add a citation to a publication. Automatically increments citation count.',
        request=AddCitationSerializer,
        examples=[
            OpenApiExample(
                'Add Citation Example',
                value={
                    'citing_title': 'Advanced Machine Learning Techniques',
                    'citing_authors': 'Smith J, Doe J',
                    'citing_doi': '10.5678/example.2024.002',
                    'citing_year': 2024,
                    'citing_journal': 'AI Research Journal'
                },
                request_only=True,
            )
        ],
        responses={
            201: AddCitationSerializer,
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def post(self, request, pk):
        try:
            author = Author.objects.get(user=request.user)
            publication = get_object_or_404(Publication, pk=pk, author=author)
            
            serializer = AddCitationSerializer(
                data=request.data,
                context={'publication': publication}
            )
            serializer.is_valid(raise_exception=True)
            citation = serializer.save()
            
            return Response({
                'message': 'Citation added successfully',
                'citation': AddCitationSerializer(citation).data
            }, status=status.HTTP_201_CREATED)
        except Author.DoesNotExist:
            return Response({'error': 'Author profile not found'}, status=status.HTTP_404_NOT_FOUND)


class AddReferenceView(APIView):
    """
    Add a reference to a publication.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Publications'],
        summary='Add Single Reference',
        description='Add a single reference to a publication.',
        request=AddReferenceSerializer,
        responses={
            201: AddReferenceSerializer,
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def post(self, request, pk):
        try:
            author = Author.objects.get(user=request.user)
            publication = get_object_or_404(Publication, pk=pk, author=author)
            
            serializer = AddReferenceSerializer(
                data=request.data,
                context={'publication': publication}
            )
            serializer.is_valid(raise_exception=True)
            reference = serializer.save()
            
            return Response({
                'message': 'Reference added successfully',
                'reference': AddReferenceSerializer(reference).data
            }, status=status.HTTP_201_CREATED)
        except Author.DoesNotExist:
            return Response({'error': 'Author profile not found'}, status=status.HTTP_404_NOT_FOUND)


class BulkAddReferencesView(APIView):
    """
    Add multiple references to a publication at once.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Publications'],
        summary='Add Multiple References',
        description='Add multiple references to a publication in bulk.',
        request=BulkReferencesSerializer,
        examples=[
            OpenApiExample(
                'Bulk References Example',
                value={
                    'references': [
                        {
                            'reference_text': 'Author A. Title of Paper. Journal Name. 2023;10(2):123-145.',
                            'reference_title': 'Title of Paper',
                            'reference_authors': 'Author A',
                            'reference_year': 2023,
                            'order': 1
                        },
                        {
                            'reference_text': 'Author B. Another Paper. Conference Proceedings. 2022.',
                            'reference_title': 'Another Paper',
                            'reference_authors': 'Author B',
                            'reference_year': 2022,
                            'order': 2
                        }
                    ]
                },
                request_only=True,
            )
        ],
        responses={
            201: OpenApiResponse(description='References added successfully'),
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def post(self, request, pk):
        try:
            author = Author.objects.get(user=request.user)
            publication = get_object_or_404(Publication, pk=pk, author=author)
            
            serializer = BulkReferencesSerializer(
                data=request.data,
                context={'publication': publication}
            )
            serializer.is_valid(raise_exception=True)
            references = serializer.save()
            
            return Response({
                'message': f'{len(references)} references added successfully',
                'count': len(references)
            }, status=status.HTTP_201_CREATED)
        except Author.DoesNotExist:
            return Response({'error': 'Author profile not found'}, status=status.HTTP_404_NOT_FOUND)


class RecordPublicationReadView(APIView):
    """
    Record a read event for a publication (increments read count).
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Publications'],
        summary='Record Read Event',
        description='Record when a publication is read. Increments the read count.',
        request=None,
        responses={
            200: OpenApiResponse(description='Read recorded'),
            404: OpenApiResponse(description='Publication not found'),
        }
    )
    def post(self, request, pk):
        publication = get_object_or_404(Publication, pk=pk, is_published=True)
        
        # Get reader info
        reader_email = request.user.email if request.user.is_authenticated else ''
        reader_ip = request.META.get('REMOTE_ADDR')
        
        # Record read event
        PublicationRead.objects.create(
            publication=publication,
            reader_email=reader_email,
            reader_ip=reader_ip
        )
        
        # Increment read count
        stats, created = PublicationStats.objects.get_or_create(publication=publication)
        stats.reads_count += 1
        stats.save()
        
        return Response({
            'message': 'Read recorded',
            'reads_count': stats.reads_count
        }, status=status.HTTP_200_OK)


class DownloadPublicationView(APIView):
    """
    Download publication PDF and increment download count.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Publications'],
        summary='Download Publication PDF',
        description='Download the PDF file of a publication. Increments download count.',
        responses={
            200: OpenApiResponse(description='PDF URL returned'),
            404: OpenApiResponse(description='Publication or PDF not found'),
        }
    )
    def get(self, request, pk):
        publication = get_object_or_404(Publication, pk=pk, is_published=True)
        
        if not publication.pdf_file:
            return Response({
                'error': 'PDF file not available for this publication'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Increment download count
        stats, created = PublicationStats.objects.get_or_create(publication=publication)
        stats.downloads_count += 1
        stats.save()
        
        # Return PDF URL
        pdf_url = request.build_absolute_uri(publication.pdf_file.url)
        
        return Response({
            'message': 'Download initiated',
            'pdf_url': pdf_url,
            'downloads_count': stats.downloads_count
        }, status=status.HTTP_200_OK)


# ==================== JOURNAL VIEWS ====================

class JournalListCreateView(generics.ListCreateAPIView):
    """
    List all journals for the authenticated institution or create a new journal.
    
    GET: List all journals of the authenticated institution
    POST: Create a new journal
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JournalCreateUpdateSerializer
        return JournalListSerializer
    
    def get_queryset(self):
        # Get journals for the authenticated institution
        try:
            institution = Institution.objects.get(user=self.request.user)
            return Journal.objects.filter(institution=institution).select_related(
                'institution', 'stats'
            ).prefetch_related('editorial_board', 'issues')
        except Institution.DoesNotExist:
            return Journal.objects.none()
    
    @extend_schema(
        tags=['Journals'],
        summary='List My Journals',
        description='Retrieve all journals for the authenticated institution.',
        responses={
            200: JournalListSerializer(many=True),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Journals'],
        summary='Create Journal',
        description='Create a new journal with all information sections and editorial board.',
        request=JournalCreateUpdateSerializer,
        examples=[
            OpenApiExample(
                'Create Journal Example',
                value={
                    'title': 'International Journal of Advanced Research',
                    'short_title': 'IJAR',
                    'issn': '1234-5678',
                    'e_issn': '9876-5432',
                    'description': 'Leading journal in advanced research',
                    'scope': 'Covers all aspects of advanced scientific research',
                    'publisher_name': 'Academic Press',
                    'frequency': 'quarterly',
                    'established_year': 2020,
                    'about_journal': 'Detailed information about the journal...',
                    'ethics_policies': 'Our ethics and editorial policies...',
                    'writing_formatting': 'Guidelines for writing and formatting...',
                    'submitting_manuscript': 'Instructions for manuscript submission...',
                    'help_support': 'Contact us for support...',
                    'contact_email': 'editor@journal.com',
                    'is_open_access': True,
                    'peer_reviewed': True
                },
                request_only=True,
            )
        ],
        responses={
            201: JournalDetailSerializer,
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        journal = serializer.save()
        
        # Return detailed response
        response_serializer = JournalDetailSerializer(journal, context={'request': request})
        return Response({
            'message': 'Journal created successfully',
            'journal': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class JournalDetailView(APIView):
    """
    Retrieve, update, or delete a specific journal.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_object(self, pk, user):
        try:
            institution = Institution.objects.get(user=user)
            return get_object_or_404(
                Journal.objects.select_related('institution', 'stats')
                .prefetch_related('editorial_board', 'issues'),
                pk=pk,
                institution=institution
            )
        except Institution.DoesNotExist:
            return None
    
    @extend_schema(
        tags=['Journals'],
        summary='Get Journal Details',
        description='Retrieve complete journal information including editorial board and stats.',
        responses={
            200: JournalDetailSerializer,
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def get(self, request, pk):
        journal = self.get_object(pk, request.user)
        if not journal:
            return Response({'error': 'Journal not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Refresh stats on every profile fetch
        stats, created = JournalStats.objects.get_or_create(journal=journal)
        stats.update_stats()
        
        serializer = JournalDetailSerializer(journal, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Journals'],
        summary='Update Journal (Partial)',
        description='Partially update journal information.',
        request=JournalCreateUpdateSerializer,
        responses={
            200: JournalDetailSerializer,
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def patch(self, request, pk):
        journal = self.get_object(pk, request.user)
        if not journal:
            return Response({'error': 'Journal not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = JournalCreateUpdateSerializer(
            journal, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        journal = serializer.save()
        
        response_serializer = JournalDetailSerializer(journal, context={'request': request})
        return Response({
            'message': 'Journal updated successfully',
            'journal': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Journals'],
        summary='Delete Journal',
        description='Permanently delete a journal and all associated data.',
        responses={
            200: OpenApiResponse(description='Journal deleted'),
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def delete(self, request, pk):
        journal = self.get_object(pk, request.user)
        if not journal:
            return Response({'error': 'Journal not found'}, status=status.HTTP_404_NOT_FOUND)
        
        title = journal.title
        journal.delete()
        
        return Response({
            'message': f'Journal "{title}" has been deleted successfully'
        }, status=status.HTTP_200_OK)


class JournalStatsView(APIView):
    """
    Get or update statistics for a journal.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Journals'],
        summary='Get Journal Stats',
        description='Retrieve statistics including impact factor, cite score, acceptance rate, etc.',
        responses={
            200: JournalStatsSerializer,
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def get(self, request, pk):
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=pk, institution=institution)
            stats, created = JournalStats.objects.get_or_create(journal=journal)
            
            serializer = JournalStatsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({'error': 'Institution profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        tags=['Journals'],
        summary='Update Journal Stats',
        description='Update journal statistics (impact factor, cite score, etc.).',
        request=JournalStatsSerializer,
        responses={
            200: JournalStatsSerializer,
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def patch(self, request, pk):
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=pk, institution=institution)
            stats, created = JournalStats.objects.get_or_create(journal=journal)
            
            serializer = JournalStatsSerializer(stats, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'message': 'Stats updated successfully',
                'stats': serializer.data
            }, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({'error': 'Institution profile not found'}, status=status.HTTP_404_NOT_FOUND)


class RefreshJournalStatsView(APIView):
    """
    Manually refresh/update journal statistics.
    
    Recalculates h-index, impact factor, cite score, total citations, reads,
    and other metrics based on current publications data.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Journals'],
        summary='Refresh Journal Statistics',
        description='Manually trigger a recalculation of all journal statistics including h-index, impact factor, cite score, total citations, reads, and recommendations. This aggregates data from all published articles in the journal.',
        responses={
            200: OpenApiResponse(
                description='Statistics updated successfully',
                response=JournalStatsSerializer,
            ),
            404: OpenApiResponse(description='Journal not found'),
            403: OpenApiResponse(description='Only journal owner can refresh stats'),
        }
    )
    def post(self, request, pk):
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=pk, institution=institution)
            stats, created = JournalStats.objects.get_or_create(journal=journal)
            stats.update_stats()
            
            serializer = JournalStatsSerializer(stats)
            return Response({
                'message': 'Statistics updated successfully',
                'stats': serializer.data
            }, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({
                'error': 'Institution profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


class EditorialBoardListCreateView(APIView):
    """
    List or add editorial board members for a journal.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Journals'],
        summary='List Editorial Board',
        description='Get all editorial board members for a journal.',
        responses={
            200: EditorialBoardMemberSerializer(many=True),
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def get(self, request, journal_pk):
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=journal_pk, institution=institution)
            members = journal.editorial_board.filter(is_active=True)
            
            serializer = EditorialBoardMemberSerializer(members, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({'error': 'Institution profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        tags=['Journals'],
        summary='Add Editorial Board Member',
        description='Add a new editorial board member to the journal.',
        request=EditorialBoardMemberSerializer,
        responses={
            201: EditorialBoardMemberSerializer,
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def post(self, request, journal_pk):
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=journal_pk, institution=institution)
            
            serializer = EditorialBoardMemberSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            member = serializer.save(journal=journal)
            
            return Response({
                'message': 'Editorial board member added successfully',
                'member': EditorialBoardMemberSerializer(member, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        except Institution.DoesNotExist:
            return Response({'error': 'Institution profile not found'}, status=status.HTTP_404_NOT_FOUND)


# ==================== ISSUE VIEWS ====================

class IssueListCreateView(generics.ListCreateAPIView):
    """
    List all issues for a journal or create a new issue.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IssueCreateUpdateSerializer
        return IssueListSerializer
    
    def get_queryset(self):
        journal_pk = self.kwargs.get('journal_pk')
        journal = get_object_or_404(Journal, pk=journal_pk)
        
        # For POST requests (create), verify institution ownership
        if self.request.method == 'POST':
            try:
                institution = Institution.objects.get(user=self.request.user)
                if journal.institution != institution:
                    return Issue.objects.none()
            except Institution.DoesNotExist:
                return Issue.objects.none()
        
        # For GET requests (list), allow anyone authenticated to view issues
        return Issue.objects.filter(journal=journal).prefetch_related('articles')
    
    @extend_schema(
        tags=['Issues'],
        summary='List Journal Issues',
        description='Retrieve all issues for a specific journal.',
        responses={
            200: IssueListSerializer(many=True),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Issues'],
        summary='Create Issue',
        description='Create a new issue for the journal.',
        request=IssueCreateUpdateSerializer,
        responses={
            201: IssueDetailSerializer,
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def post(self, request, *args, **kwargs):
        journal_pk = self.kwargs.get('journal_pk')
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=journal_pk, institution=institution)
            
            serializer = self.get_serializer(data=request.data, context={'request': request, 'journal': journal})
            serializer.is_valid(raise_exception=True)
            issue = serializer.save()
            
            response_serializer = IssueDetailSerializer(issue, context={'request': request})
            return Response({
                'message': 'Issue created successfully',
                'issue': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except Institution.DoesNotExist:
            return Response({'error': 'Institution profile not found'}, status=status.HTTP_404_NOT_FOUND)


class IssueDetailView(APIView):
    """
    Retrieve, update, or delete a specific issue.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_object(self, journal_pk, pk, user):
        try:
            institution = Institution.objects.get(user=user)
            journal = get_object_or_404(Journal, pk=journal_pk, institution=institution)
            return get_object_or_404(
                Issue.objects.prefetch_related('articles'),
                pk=pk,
                journal=journal
            )
        except Institution.DoesNotExist:
            return None
    
    @extend_schema(
        tags=['Issues'],
        summary='Get Issue Details',
        description='Retrieve complete issue information including all articles.',
        responses={
            200: IssueDetailSerializer,
            404: OpenApiResponse(description='Issue not found'),
        }
    )
    def get(self, request, journal_pk, pk):
        issue = self.get_object(journal_pk, pk, request.user)
        if not issue:
            return Response({'error': 'Issue not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = IssueDetailSerializer(issue, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Issues'],
        summary='Update Issue',
        description='Update issue information.',
        request=IssueCreateUpdateSerializer,
        responses={
            200: IssueDetailSerializer,
            404: OpenApiResponse(description='Issue not found'),
        }
    )
    def patch(self, request, journal_pk, pk):
        issue = self.get_object(journal_pk, pk, request.user)
        if not issue:
            return Response({'error': 'Issue not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = IssueCreateUpdateSerializer(
            issue, 
            data=request.data, 
            partial=True,
            context={'request': request, 'journal': issue.journal}
        )
        serializer.is_valid(raise_exception=True)
        issue = serializer.save()
        
        response_serializer = IssueDetailSerializer(issue, context={'request': request})
        return Response({
            'message': 'Issue updated successfully',
            'issue': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Issues'],
        summary='Delete Issue',
        description='Permanently delete an issue.',
        responses={
            200: OpenApiResponse(description='Issue deleted'),
            404: OpenApiResponse(description='Issue not found'),
        }
    )
    def delete(self, request, journal_pk, pk):
        issue = self.get_object(journal_pk, pk, request.user)
        if not issue:
            return Response({'error': 'Issue not found'}, status=status.HTTP_404_NOT_FOUND)
        
        issue_info = f"Vol. {issue.volume}, Issue {issue.issue_number}"
        
        # Update journal stats
        stats = issue.journal.stats
        if stats.total_issues > 0:
            stats.total_issues -= 1
            stats.save()
        
        issue.delete()
        
        return Response({
            'message': f'Issue "{issue_info}" has been deleted successfully'
        }, status=status.HTTP_200_OK)


class AddArticleToIssueView(APIView):
    """
    Add an article to a journal issue.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Issues'],
        summary='Add Article to Issue',
        description='Add an existing publication to a journal issue.',
        request=AddArticleToIssueSerializer,
        examples=[
            OpenApiExample(
                'Add Article Example',
                value={
                    'publication_id': 1,
                    'order': 1,
                    'section': 'Research Articles'
                },
                request_only=True,
            )
        ],
        responses={
            201: OpenApiResponse(description='Article added to issue'),
            404: OpenApiResponse(description='Issue or publication not found'),
        }
    )
    def post(self, request, journal_pk, issue_pk):
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=journal_pk, institution=institution)
            issue = get_object_or_404(Issue, pk=issue_pk, journal=journal)
            
            serializer = AddArticleToIssueSerializer(
                data=request.data,
                context={'issue': issue}
            )
            serializer.is_valid(raise_exception=True)
            article = serializer.save()
            
            # Update journal stats
            stats, created = JournalStats.objects.get_or_create(journal=journal)
            stats.total_articles += 1
            stats.save()
            
            return Response({
                'message': 'Article added to issue successfully',
                'article': {
                    'id': article.id,
                    'publication_id': article.publication.id,
                    'order': article.order,
                    'section': article.section
                }
            }, status=status.HTTP_201_CREATED)
        except Institution.DoesNotExist:
            return Response({'error': 'Institution profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Publication.DoesNotExist:
            return Response({'error': 'Publication not found'}, status=status.HTTP_404_NOT_FOUND)


# ==================== JOURNAL QUESTIONNAIRE VIEWS ====================

class JournalQuestionnaireCreateView(APIView):
    """
    Create or retrieve questionnaire for a journal.
    
    GET: Retrieve existing questionnaire for a journal
    POST: Create a new questionnaire for a journal
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Journal Questionnaire'],
        summary='Get Journal Questionnaire',
        description='Retrieve the questionnaire for a specific journal.',
        responses={
            200: JournalQuestionnaireDetailSerializer,
            404: OpenApiResponse(description='Journal or questionnaire not found'),
        }
    )
    def get(self, request, journal_pk):
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=journal_pk, institution=institution)
            
            try:
                questionnaire = JournalQuestionnaire.objects.get(journal=journal)
                serializer = JournalQuestionnaireDetailSerializer(questionnaire)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except JournalQuestionnaire.DoesNotExist:
                return Response({
                    'error': 'No questionnaire found for this journal',
                    'message': 'Please create a questionnaire using POST method'
                }, status=status.HTTP_404_NOT_FOUND)
        
        except Institution.DoesNotExist:
            return Response({'error': 'Institution profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        tags=['Journal Questionnaire'],
        summary='Create Journal Questionnaire',
        description='Create a comprehensive questionnaire for a journal with 12 sections of information.',
        request=JournalQuestionnaireCreateUpdateSerializer,
        examples=[
            OpenApiExample(
                'Create Questionnaire Example',
                value={
                    'journal': 1,
                    'journal_title': 'International Journal of Advanced Research',
                    'issn': '1234-5678',
                    'e_issn': '9876-5432',
                    'publisher_name': 'Academic Press',
                    'publisher_country': 'United States',
                    'year_first_publication': 2020,
                    'publication_frequency': 'quarterly',
                    'publication_format': 'both',
                    'journal_website_url': 'https://journal.example.com',
                    'contact_email': 'editor@journal.com',
                    'main_discipline': 'Computer Science',
                    'secondary_disciplines': 'Artificial Intelligence, Machine Learning',
                    'aims_and_scope': 'The journal focuses on...',
                    'publishes_original_research': True,
                    'publishes_review_articles': True,
                    'publishes_case_studies': False,
                    'publishes_short_communications': True,
                    'publishes_other': '',
                    'editor_in_chief_name': 'Dr. John Smith',
                    'editor_in_chief_affiliation': 'MIT',
                    'editor_in_chief_country': 'United States',
                    'editorial_board_members_count': 25,
                    'editorial_board_countries': 'USA, UK, Germany, France, China',
                    'foreign_board_members_percentage': 60.0,
                    'board_details_published': True,
                    'uses_peer_review': True,
                    'peer_review_type': 'double_blind',
                    'reviewers_per_manuscript': 2,
                    'average_review_time_weeks': 4,
                    'reviewers_external': True,
                    'peer_review_procedure_published': True,
                    'peer_review_procedure_url': 'https://journal.example.com/peer-review',
                    'follows_publication_ethics': True,
                    'ethics_based_on_cope': True,
                    'ethics_based_on_icmje': True,
                    'ethics_other_guidelines': '',
                    'uses_plagiarism_detection': True,
                    'plagiarism_software_name': 'iThenticate',
                    'has_retraction_policy': True,
                    'retraction_policy_url': 'https://journal.example.com/retraction-policy',
                    'has_conflict_of_interest_policy': True,
                    'conflict_of_interest_policy_url': 'https://journal.example.com/coi-policy',
                    'issues_published_in_year': 4,
                    'all_issues_published_on_time': True,
                    'articles_published_in_year': 120,
                    'submissions_rejected': 200,
                    'average_acceptance_rate': 37.5,
                    'total_authors_in_year': 350,
                    'foreign_authors_count': 210,
                    'author_countries_count': 45,
                    'foreign_authors_percentage': 60.0,
                    'encourages_international_submissions': True,
                    'is_open_access': True,
                    'oa_model': 'gold',
                    'has_apc': True,
                    'apc_amount': 2000.00,
                    'apc_currency': 'USD',
                    'license_type': 'cc_by',
                    'assigns_dois': True,
                    'doi_registration_agency': 'Crossref',
                    'metadata_standards_used': 'Dublin Core, JATS',
                    'uses_online_submission_system': True,
                    'submission_system_name': 'Open Journal Systems',
                    'digital_archiving_system': 'lockss',
                    'other_archiving_system': '',
                    'indexed_databases': 'Scopus, Web of Science, Google Scholar',
                    'year_first_indexed': 2021,
                    'indexed_in_google_scholar': True,
                    'indexed_in_doaj': True,
                    'indexed_in_scopus': True,
                    'indexed_in_web_of_science': False,
                    'abstracting_services': 'Chemical Abstracts, INSPEC',
                    'author_guidelines_available': True,
                    'peer_review_rules_available': True,
                    'apcs_clearly_stated': True,
                    'journal_archive_accessible': True,
                    'data_is_verifiable': True,
                    'data_matches_website': True,
                    'consent_to_evaluation': True,
                    'completed_by_name': 'Jane Doe',
                    'completed_by_role': 'Managing Editor'
                },
                request_only=True,
            )
        ],
        responses={
            201: JournalQuestionnaireDetailSerializer,
            400: OpenApiResponse(description='Validation error or questionnaire already exists'),
        }
    )
    def post(self, request, journal_pk):
        try:
            institution = Institution.objects.get(user=request.user)
            journal = get_object_or_404(Journal, pk=journal_pk, institution=institution)
            
            # Set journal in request data
            data = request.data.copy()
            data['journal'] = journal.id
            
            serializer = JournalQuestionnaireCreateUpdateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            questionnaire = serializer.save()
            
            response_serializer = JournalQuestionnaireDetailSerializer(questionnaire)
            return Response({
                'message': 'Journal questionnaire created successfully',
                'questionnaire': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Institution.DoesNotExist:
            return Response({'error': 'Institution profile not found'}, status=status.HTTP_404_NOT_FOUND)


class JournalQuestionnaireDetailView(APIView):
    """
    Retrieve, update, or delete a specific journal questionnaire.
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        try:
            institution = Institution.objects.get(user=user)
            return get_object_or_404(
                JournalQuestionnaire.objects.select_related('journal'),
                pk=pk,
                journal__institution=institution
            )
        except Institution.DoesNotExist:
            return None
    
    @extend_schema(
        tags=['Journal Questionnaire'],
        summary='Get Questionnaire Details',
        description='Retrieve complete questionnaire information.',
        responses={
            200: JournalQuestionnaireDetailSerializer,
            404: OpenApiResponse(description='Questionnaire not found'),
        }
    )
    def get(self, request, pk):
        questionnaire = self.get_object(pk, request.user)
        if not questionnaire:
            return Response({'error': 'Questionnaire not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = JournalQuestionnaireDetailSerializer(questionnaire)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Journal Questionnaire'],
        summary='Update Questionnaire (Partial)',
        description='Partially update questionnaire information.',
        request=JournalQuestionnaireCreateUpdateSerializer,
        responses={
            200: JournalQuestionnaireDetailSerializer,
            404: OpenApiResponse(description='Questionnaire not found'),
        }
    )
    def patch(self, request, pk):
        questionnaire = self.get_object(pk, request.user)
        if not questionnaire:
            return Response({'error': 'Questionnaire not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = JournalQuestionnaireCreateUpdateSerializer(
            questionnaire,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        questionnaire = serializer.save()
        
        response_serializer = JournalQuestionnaireDetailSerializer(questionnaire)
        return Response({
            'message': 'Questionnaire updated successfully',
            'questionnaire': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Journal Questionnaire'],
        summary='Update Questionnaire (Full)',
        description='Fully update questionnaire information.',
        request=JournalQuestionnaireCreateUpdateSerializer,
        responses={
            200: JournalQuestionnaireDetailSerializer,
            404: OpenApiResponse(description='Questionnaire not found'),
        }
    )
    def put(self, request, pk):
        questionnaire = self.get_object(pk, request.user)
        if not questionnaire:
            return Response({'error': 'Questionnaire not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = JournalQuestionnaireCreateUpdateSerializer(
            questionnaire,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        questionnaire = serializer.save()
        
        response_serializer = JournalQuestionnaireDetailSerializer(questionnaire)
        return Response({
            'message': 'Questionnaire updated successfully',
            'questionnaire': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Journal Questionnaire'],
        summary='Delete Questionnaire',
        description='Delete a journal questionnaire.',
        responses={
            200: OpenApiResponse(description='Questionnaire deleted'),
            404: OpenApiResponse(description='Questionnaire not found'),
        }
    )
    def delete(self, request, pk):
        questionnaire = self.get_object(pk, request.user)
        if not questionnaire:
            return Response({'error': 'Questionnaire not found'}, status=status.HTTP_404_NOT_FOUND)
        
        journal_title = questionnaire.journal.title
        questionnaire.delete()
        
        return Response({
            'message': f'Questionnaire for "{journal_title}" has been deleted successfully'
        }, status=status.HTTP_200_OK)


class JournalQuestionnaireListView(generics.ListAPIView):
    """
    List all questionnaires for the authenticated institution's journals.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = JournalQuestionnaireListSerializer
    
    def get_queryset(self):
        try:
            institution = Institution.objects.get(user=self.request.user)
            return JournalQuestionnaire.objects.filter(
                journal__institution=institution
            ).select_related('journal')
        except Institution.DoesNotExist:
            return JournalQuestionnaire.objects.none()
    
    @extend_schema(
        tags=['Journal Questionnaire'],
        summary='List All Questionnaires',
        description='Retrieve all questionnaires for the authenticated institution.',
        responses={
            200: JournalQuestionnaireListSerializer(many=True),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ==================== PUBLIC PUBLICATION VIEWS ====================

class PublicPublicationsListView(generics.ListAPIView):
    """
    List all published publications publicly (no authentication required).
    Supports filtering by publication type, topic, author, and search.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicationListSerializer
    
    def get_queryset(self):
        queryset = Publication.objects.filter(
            is_published=True
        ).select_related(
            'author', 'author__user', 'stats', 'topic_branch', 'topic_branch__topic'
        ).prefetch_related('mesh_terms', 'citations', 'references')
        
        # Filter by publication type
        pub_type = self.request.query_params.get('type', None)
        if pub_type:
            queryset = queryset.filter(publication_type=pub_type)
        
        # Filter by topic branch
        topic_branch_id = self.request.query_params.get('topic_branch', None)
        if topic_branch_id:
            queryset = queryset.filter(topic_branch_id=topic_branch_id)
        
        # Filter by author
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Search by title, abstract, or journal name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(abstract__icontains=search) |
                Q(journal_name__icontains=search) |
                Q(co_authors__icontains=search)
            )
        
        return queryset
    
    @extend_schema(
        tags=['Public Publications'],
        summary='List All Publications (Public)',
        description='Retrieve all published publications. No authentication required. Supports filtering and search.',
        parameters=[
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by publication type (e.g., journal_article, conference_paper)',
                required=False,
            ),
            OpenApiParameter(
                name='topic_branch',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by topic branch ID',
                required=False,
            ),
            OpenApiParameter(
                name='author',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by author ID',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, abstract, journal name, or co-authors',
                required=False,
            ),
        ],
        responses={200: PublicationListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class JournalPublicationsListView(generics.ListAPIView):
    """
    List all publications associated with a specific journal (public access).
    Publications are linked to journals through issues.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicationListSerializer
    
    def get_queryset(self):
        journal_pk = self.kwargs.get('journal_pk')
        
        # Get all publications that are part of any issue in this journal
        queryset = Publication.objects.filter(
            issue_appearances__issue__journal_id=journal_pk,
            is_published=True
        ).distinct().select_related(
            'author', 'author__user', 'stats', 'topic_branch', 'topic_branch__topic'
        ).prefetch_related('mesh_terms', 'citations', 'references', 'issue_appearances')
        
        # Filter by publication type
        pub_type = self.request.query_params.get('type', None)
        if pub_type:
            queryset = queryset.filter(publication_type=pub_type)
        
        # Filter by issue
        issue_id = self.request.query_params.get('issue', None)
        if issue_id:
            queryset = queryset.filter(issue_appearances__issue_id=issue_id)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(abstract__icontains=search) |
                Q(co_authors__icontains=search)
            )
        
        return queryset
    
    @extend_schema(
        tags=['Public Publications'],
        summary='List Journal Publications (Public)',
        description='Retrieve all published publications for a specific journal. No authentication required.',
        parameters=[
            OpenApiParameter(
                name='journal_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Journal ID',
                required=True,
            ),
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by publication type',
                required=False,
            ),
            OpenApiParameter(
                name='issue',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by issue ID',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, abstract, or co-authors',
                required=False,
            ),
        ],
        responses={
            200: PublicationListSerializer(many=True),
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def get(self, request, *args, **kwargs):
        # Verify journal exists
        journal_pk = self.kwargs.get('journal_pk')
        if not Journal.objects.filter(pk=journal_pk).exists():
            return Response(
                {'error': 'Journal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().get(request, *args, **kwargs)


class PublicPublicationDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single published publication (public access).
    No authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicationDetailSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        # Only return published publications
        return Publication.objects.filter(
            is_published=True
        ).select_related(
            'author', 'author__user', 'stats', 'topic_branch', 'topic_branch__topic', 'erratum_from'
        ).prefetch_related('mesh_terms', 'citations', 'references', 'link_outs')
    
    @extend_schema(
        tags=['Public Publications'],
        summary='Get Publication Details (Public)',
        description='Retrieve complete information about a single published publication. No authentication required.',
        responses={
            200: PublicationDetailSerializer,
            404: OpenApiResponse(description='Publication not found or not published'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicJournalsListView(generics.ListAPIView):
    """
    List all active journals publicly (no authentication required).
    Supports filtering and search.
    """
    permission_classes = [AllowAny]
    serializer_class = JournalListSerializer
    
    def get_queryset(self):
        queryset = Journal.objects.filter(
            is_active=True
        ).select_related('institution', 'stats').prefetch_related('editorial_board', 'issues')
        
        # Filter by institution
        institution_id = self.request.query_params.get('institution', None)
        if institution_id:
            queryset = queryset.filter(institution_id=institution_id)
        
        # Filter by open access
        is_open_access = self.request.query_params.get('open_access', None)
        if is_open_access is not None:
            queryset = queryset.filter(is_open_access=is_open_access.lower() == 'true')
        
        # Filter by peer reviewed
        peer_reviewed = self.request.query_params.get('peer_reviewed', None)
        if peer_reviewed is not None:
            queryset = queryset.filter(peer_reviewed=peer_reviewed.lower() == 'true')
        
        # Search by title or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(short_title__icontains=search) |
                Q(description__icontains=search) |
                Q(publisher_name__icontains=search)
            )
        
        return queryset
    
    @extend_schema(
        tags=['Public Journals'],
        summary='List All Journals (Public)',
        description='Retrieve all active journals. No authentication required. Supports filtering and search.',
        parameters=[
            OpenApiParameter(
                name='institution',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by institution ID',
                required=False,
            ),
            OpenApiParameter(
                name='open_access',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by open access status (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='peer_reviewed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by peer reviewed status (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, description, or publisher name',
                required=False,
            ),
        ],
        responses={200: JournalListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicJournalDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single journal (public access).
    No authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = JournalDetailSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        # Only return active journals
        return Journal.objects.filter(
            is_active=True
        ).select_related('institution', 'stats').prefetch_related('editorial_board', 'issues')
    
    @extend_schema(
        tags=['Public Journals'],
        summary='Get Journal Details (Public)',
        description='Retrieve complete information about a single journal. No authentication required.',
        responses={
            200: JournalDetailSerializer,
            404: OpenApiResponse(description='Journal not found or not active'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ==================== PUBLIC INSTITUTION VIEWS ====================

class PublicInstitutionsListView(generics.ListAPIView):
    """
    List all institutions publicly (no authentication required).
    Supports filtering and search.
    """
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        from users.models import Institution
        queryset = Institution.objects.select_related('user', 'stats').prefetch_related('journals')
        
        # Filter by country
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country__iexact=country)
        
        # Filter by institution type
        institution_type = self.request.query_params.get('type', None)
        if institution_type:
            queryset = queryset.filter(institution_type=institution_type)
        
        # Search by name, city, or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(institution_name__icontains=search) |
                Q(city__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        from users.serializers import InstitutionListSerializer
        return InstitutionListSerializer
    
    @extend_schema(
        tags=['Public Institutions'],
        summary='List All Institutions (Public)',
        description='Retrieve all institutions. No authentication required. Supports filtering and search.',
        parameters=[
            OpenApiParameter(
                name='country',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by country name',
                required=False,
            ),
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by institution type (university, research_institute, hospital, etc.)',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in institution name, city, or description',
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(description='List of institutions')}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicInstitutionDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single institution (public access).
    No authentication required.
    """
    permission_classes = [AllowAny]
    lookup_field = 'pk'
    
    def get_queryset(self):
        from users.models import Institution
        return Institution.objects.select_related('user', 'stats').prefetch_related('journals')
    
    def get_serializer_class(self):
        from users.serializers import InstitutionDetailSerializer
        return InstitutionDetailSerializer
    
    @extend_schema(
        tags=['Public Institutions'],
        summary='Get Institution Details (Public)',
        description='Retrieve complete information about a single institution including journals and stats. No authentication required.',
        responses={
            200: OpenApiResponse(description='Institution details'),
            404: OpenApiResponse(description='Institution not found'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ==================== PUBLIC AUTHOR VIEWS ====================

class PublicAuthorsListView(generics.ListAPIView):
    """
    List all authors publicly (no authentication required).
    Supports filtering and search.
    """
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        from users.models import Author
        queryset = Author.objects.select_related('user', 'stats')
        
        # Filter by institute
        institute = self.request.query_params.get('institute', None)
        if institute:
            queryset = queryset.filter(institute__icontains=institute)
        
        # Filter by designation
        designation = self.request.query_params.get('designation', None)
        if designation:
            queryset = queryset.filter(designation__icontains=designation)
        
        # Search by name, institute, or research interests
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(institute__icontains=search) |
                Q(research_interests__icontains=search) |
                Q(bio__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        from users.serializers import AuthorListSerializer
        return AuthorListSerializer
    
    @extend_schema(
        tags=['Public Authors'],
        summary='List All Authors (Public)',
        description='Retrieve all authors. No authentication required. Supports filtering and search.',
        parameters=[
            OpenApiParameter(
                name='institute',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by institute name',
                required=False,
            ),
            OpenApiParameter(
                name='designation',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by designation',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in author name, institute, bio, or research interests',
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(description='List of authors')}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicAuthorDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single author (public access).
    No authentication required.
    """
    permission_classes = [AllowAny]
    lookup_field = 'pk'
    
    def get_queryset(self):
        from users.models import Author
        return Author.objects.select_related('user', 'stats')
    
    def get_serializer_class(self):
        from users.serializers import AuthorDetailSerializer
        return AuthorDetailSerializer
    
    @extend_schema(
        tags=['Public Authors'],
        summary='Get Author Details (Public)',
        description='Retrieve complete information about a single author including stats, publications count, and co-authors. No authentication required.',
        responses={
            200: OpenApiResponse(description='Author details'),
            404: OpenApiResponse(description='Author not found'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

