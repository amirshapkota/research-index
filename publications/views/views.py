from rest_framework import generics, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

from ..models import (
    Publication, MeSHTerm, PublicationStats, 
    Citation, Reference, LinkOut, PublicationRead,
    Journal, EditorialBoardMember, JournalStats, Issue, IssueArticle,
    Topic, TopicBranch, JournalQuestionnaire
)
from ..serializers import (
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
from ..services import CrossrefCitationAPI
from users.models import Author, Institution
import logging
import time

logger = logging.getLogger(__name__)


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
    Supports comprehensive filtering by publication type, topic, author, year, journal, and more.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicationListSerializer
    
    def get_queryset(self):
        queryset = Publication.objects.filter(
            is_published=True
        ).select_related(
            'author', 'author__user', 'stats', 'topic_branch', 'topic_branch__topic', 'journal'
        ).prefetch_related('mesh_terms', 'citations', 'references')
        
        # Filter by publication type
        pub_type = self.request.query_params.get('type', None)
        if pub_type:
            queryset = queryset.filter(publication_type=pub_type)
        
        # Filter by topic branch
        topic_branch_id = self.request.query_params.get('topic_branch', None)
        if topic_branch_id:
            queryset = queryset.filter(topic_branch_id=topic_branch_id)
        
        # Filter by topic (parent topic)
        topic_id = self.request.query_params.get('topic', None)
        if topic_id:
            queryset = queryset.filter(topic_branch__topic_id=topic_id)
        
        # Filter by author
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Filter by journal
        journal_id = self.request.query_params.get('journal', None)
        if journal_id:
            queryset = queryset.filter(journal_id=journal_id)
        
        # Filter by publication year
        year = self.request.query_params.get('year', None)
        if year:
            try:
                queryset = queryset.filter(published_date__year=int(year))
            except ValueError:
                pass  # Ignore invalid year values
        
        # Filter by year range
        year_from = self.request.query_params.get('year_from', None)
        year_to = self.request.query_params.get('year_to', None)
        if year_from:
            try:
                queryset = queryset.filter(published_date__year__gte=int(year_from))
            except ValueError:
                pass
        if year_to:
            try:
                queryset = queryset.filter(published_date__year__lte=int(year_to))
            except ValueError:
                pass
        
        # Filter by publisher
        publisher = self.request.query_params.get('publisher', None)
        if publisher:
            queryset = queryset.filter(publisher__icontains=publisher)
        
        # Filter by citations count (minimum)
        min_citations = self.request.query_params.get('min_citations', None)
        if min_citations:
            try:
                queryset = queryset.filter(stats__citations_count__gte=int(min_citations))
            except ValueError:
                pass
        
        # Filter by h-index range on stats
        h_index_min = self.request.query_params.get('h_index_min', None)
        h_index_max = self.request.query_params.get('h_index_max', None)
        if h_index_min:
            try:
                queryset = queryset.filter(author__stats__h_index__gte=int(h_index_min))
            except ValueError:
                pass
        if h_index_max:
            try:
                queryset = queryset.filter(author__stats__h_index__lte=int(h_index_max))
            except ValueError:
                pass
        
        # Filter by DOI presence
        has_doi = self.request.query_params.get('has_doi', None)
        if has_doi and has_doi.lower() in ['true', '1', 'yes']:
            queryset = queryset.exclude(doi='')
        elif has_doi and has_doi.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(doi='')
        
        # Filter by PDF availability
        has_pdf = self.request.query_params.get('has_pdf', None)
        if has_pdf and has_pdf.lower() in ['true', '1', 'yes']:
            queryset = queryset.exclude(pdf_file='')
        elif has_pdf and has_pdf.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(Q(pdf_file='') | Q(pdf_file__isnull=True))
        
        # Search by title, abstract, doi, journal title, co-authors, or publisher
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(abstract__icontains=search) |
                Q(doi__icontains=search) |
                Q(journal__title__icontains=search) |
                Q(co_authors__icontains=search) |
                Q(publisher__icontains=search) |
                Q(author__full_name__icontains=search)
            )
        
        return queryset.distinct()
    
    @extend_schema(
        tags=['Public Publications'],
        summary='List All Publications (Public)',
        description='Retrieve all published publications. No authentication required. Supports comprehensive filtering and search.',
        parameters=[
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by publication type (journal_article, conference_paper, book_chapter, preprint, thesis, technical_report, poster, presentation, book, review, other)',
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
                name='topic',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by parent topic ID',
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
                name='journal',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by journal ID',
                required=False,
            ),
            OpenApiParameter(
                name='year',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by specific publication year',
                required=False,
            ),
            OpenApiParameter(
                name='year_from',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter publications from this year onwards',
                required=False,
            ),
            OpenApiParameter(
                name='year_to',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter publications up to this year',
                required=False,
            ),
            OpenApiParameter(
                name='publisher',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by publisher name (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='min_citations',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter publications with at least this many citations',
                required=False,
            ),
            OpenApiParameter(
                name='h_index_min',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by minimum h-index of the author',
                required=False,
            ),
            OpenApiParameter(
                name='h_index_max',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by maximum h-index of the author',
                required=False,
            ),
            OpenApiParameter(
                name='has_doi',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by DOI availability (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='has_pdf',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by PDF availability (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, abstract, DOI, journal name, co-authors, publisher, or author name',
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
        ).select_related('institution', 'stats', 'questionnaire').prefetch_related('editorial_board', 'issues')
        
        # Filter by institution
        institution_id = self.request.query_params.get('institution', None)
        institutions = self.request.query_params.get('institutions', None)
        if institution_id:
            queryset = queryset.filter(institution_id=institution_id)
        elif institutions:
            queryset = queryset.filter(institution__institution_name__icontains=institutions)
        
        # Filter by access type (open access)
        access_type = self.request.query_params.get('access_type', None)
        is_open_access = self.request.query_params.get('open_access', None)
        if access_type:
            if access_type.lower() in ['open_access', 'open access', 'true']:
                queryset = queryset.filter(is_open_access=True)
            elif access_type.lower() in ['subscription', 'false']:
                queryset = queryset.filter(is_open_access=False)
        elif is_open_access is not None:
            queryset = queryset.filter(is_open_access=is_open_access.lower() == 'true')
        
        # Filter by category/discipline
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(
                Q(questionnaire__main_discipline__icontains=category) |
                Q(questionnaire__secondary_disciplines__icontains=category)
            )
        
        # Filter by language
        language = self.request.query_params.get('language', None)
        if language:
            queryset = queryset.filter(language__icontains=language)
        
        # Filter by license type
        license = self.request.query_params.get('license', None)
        if license:
            queryset = queryset.filter(questionnaire__license_type__icontains=license)
        
        # Filter by year (established year)
        years = self.request.query_params.get('years', None)
        if years:
            try:
                year = int(years)
                queryset = queryset.filter(established_year=year)
            except ValueError:
                pass
        
        # Filter by country (through institution)
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(institution__country__icontains=country)
        
        # Filter by peer review type
        peer_review = self.request.query_params.get('peer_review', None)
        peer_reviewed = self.request.query_params.get('peer_reviewed', None)
        if peer_review:
            queryset = queryset.filter(questionnaire__peer_review_type__icontains=peer_review)
        elif peer_reviewed is not None:
            queryset = queryset.filter(peer_reviewed=peer_reviewed.lower() == 'true')
        
        # Filter by impact factor (minimum threshold)
        impact_factor = self.request.query_params.get('impact_factor', None)
        if impact_factor:
            try:
                min_impact = float(impact_factor)
                queryset = queryset.filter(stats__impact_factor__gte=min_impact)
            except (ValueError, TypeError):
                pass
        
        # Filter by CiteScore (minimum threshold)
        cite_score = self.request.query_params.get('cite_score', None)
        if cite_score:
            try:
                min_cite = float(cite_score)
                queryset = queryset.filter(stats__cite_score__gte=min_cite)
            except (ValueError, TypeError):
                pass
        
        # Filter by time to first decision (maximum weeks)
        time_to_decision = self.request.query_params.get('time_to_decision', None)
        if time_to_decision:
            try:
                max_weeks = int(time_to_decision)
                queryset = queryset.filter(questionnaire__average_review_time_weeks__lte=max_weeks)
            except (ValueError, TypeError):
                pass
        
        # Filter by time to acceptance (maximum days)
        time_to_acceptance = self.request.query_params.get('time_to_acceptance', None)
        if time_to_acceptance:
            try:
                max_days = int(time_to_acceptance)
                queryset = queryset.filter(stats__average_review_time__lte=max_days)
            except (ValueError, TypeError):
                pass
        
        # Search by title or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(short_title__icontains=search) |
                Q(description__icontains=search) |
                Q(publisher_name__icontains=search)
            )
        
        return queryset.distinct()
    
    @extend_schema(
        tags=['Public Journals'],
        summary='List All Journals (Public)',
        description='Retrieve all active journals. No authentication required. Supports comprehensive filtering and search.',
        parameters=[
            OpenApiParameter(
                name='institution',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by institution ID',
                required=False,
            ),
            OpenApiParameter(
                name='institutions',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by institution name (partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='access_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by access type (open_access, subscription)',
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
                name='category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by category/discipline (partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='language',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by language (partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='license',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by license type (cc_by, cc_by_sa, cc_by_nc, etc.)',
                required=False,
            ),
            OpenApiParameter(
                name='years',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by established year',
                required=False,
            ),
            OpenApiParameter(
                name='country',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by country (partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='peer_review',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by peer review type (single_blind, double_blind, open, etc.)',
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
                name='impact_factor',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Filter by minimum impact factor (e.g., 1.5 returns journals with IF >= 1.5)',
                required=False,
            ),
            OpenApiParameter(
                name='cite_score',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Filter by minimum CiteScore (e.g., 2.0 returns journals with CiteScore >= 2.0)',
                required=False,
            ),
            OpenApiParameter(
                name='time_to_decision',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by maximum time to first decision in weeks (e.g., 4 returns journals with <= 4 weeks)',
                required=False,
            ),
            OpenApiParameter(
                name='time_to_acceptance',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by maximum time to acceptance in days (e.g., 30 returns journals with <= 30 days)',
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


class PublicJournalIssuesView(generics.ListAPIView):
    """
    List all issues for a specific journal (public access).
    No authentication required. Returns paginated results.
    """
    permission_classes = [AllowAny]
    serializer_class = IssueListSerializer
    
    def get_queryset(self):
        journal_pk = self.kwargs.get('journal_pk')
        queryset = Issue.objects.filter(
            journal_id=journal_pk,
            journal__is_active=True
        ).select_related('journal').prefetch_related('articles').order_by(
            '-volume', '-issue_number', '-publication_date'
        )
        
        # Apply filters
        # Filter by year
        year = self.request.query_params.get('year', None)
        if year:
            queryset = queryset.filter(publication_date__year=year)
        
        # Filter by volume
        volume = self.request.query_params.get('volume', None)
        if volume:
            queryset = queryset.filter(volume=volume)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search in title and description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    @extend_schema(
        tags=['Public Journals'],
        summary='List Journal Issues (Public)',
        description='Retrieve paginated issues for a specific journal. No authentication required. Returns issues ordered by volume and issue number (newest first). Supports pagination, filtering by year, volume, status, and search.',
        parameters=[
            OpenApiParameter(
                name='journal_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Journal ID',
                required=True,
            ),
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number for pagination',
                required=False,
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of results per page (default: 10)',
                required=False,
            ),
            OpenApiParameter(
                name='year',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by publication year',
                required=False,
            ),
            OpenApiParameter(
                name='volume',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by volume number',
                required=False,
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by status (draft, published, archived)',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title and description',
                required=False,
            ),
        ],
        responses={
            200: IssueListSerializer(many=True),
            404: OpenApiResponse(description='Journal not found or not active'),
        }
    )
    def get(self, request, *args, **kwargs):
        # Check if journal exists and is active
        journal_pk = self.kwargs.get('journal_pk')
        if not Journal.objects.filter(pk=journal_pk, is_active=True).exists():
            return Response({
                'error': 'Journal not found or not active'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Use the default list method which handles pagination automatically
        return super().list(request, *args, **kwargs)


class PublicJournalIssueDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single issue with all its articles (public access).
    No authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = IssueDetailSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        journal_pk = self.kwargs.get('journal_pk')
        # Only return issues for active journals
        return Issue.objects.filter(
            journal_id=journal_pk,
            journal__is_active=True
        ).select_related('journal').prefetch_related('articles', 'articles__publication')
    
    @extend_schema(
        tags=['Public Journals'],
        summary='Get Issue Details (Public)',
        description='Retrieve complete information about a single journal issue including all articles. No authentication required.',
        parameters=[
            OpenApiParameter(
                name='journal_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Journal ID',
                required=True,
            ),
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Issue ID',
                required=True,
            ),
        ],
        responses={
            200: IssueDetailSerializer,
            404: OpenApiResponse(description='Issue not found or journal not active'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicJournalVolumesView(APIView):
    """
    Get all volumes with issues and articles for a journal (public access).
    Returns data grouped by volume with nested issues and articles.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Public Journals'],
        summary='Get Journal Volumes with Issues and Articles (Public)',
        description='Retrieve all volumes for a journal, grouped with their issues and articles. No authentication required.',
        parameters=[
            OpenApiParameter(
                name='journal_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Journal ID',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Volumes with issues and articles',
                response={
                    'type': 'object',
                    'properties': {
                        'journal_id': {'type': 'integer'},
                        'journal_title': {'type': 'string'},
                        'volumes': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'volume': {'type': 'integer'},
                                    'year': {'type': 'integer'},
                                    'issues_count': {'type': 'integer'},
                                    'articles_count': {'type': 'integer'},
                                    'issues': {'type': 'array'}
                                }
                            }
                        }
                    }
                }
            ),
            404: OpenApiResponse(description='Journal not found or not active'),
        }
    )
    def get(self, request, journal_pk):
        from collections import defaultdict
        from publications.serializers import IssueWithArticlesSerializer
        
        # Check if journal exists and is active
        journal = get_object_or_404(Journal, pk=journal_pk, is_active=True)
        
        # Get all issues for this journal with articles
        issues = Issue.objects.filter(
            journal=journal,
            status='published'
        ).select_related('journal').prefetch_related(
            'articles',
            'articles__publication',
            'articles__publication__author'
        ).order_by('-volume', '-issue_number')
        
        # Group issues by volume
        volumes_dict = defaultdict(list)
        for issue in issues:
            volumes_dict[issue.volume].append(issue)
        
        # Build response data
        volumes_data = []
        for volume_num in sorted(volumes_dict.keys(), reverse=True):
            volume_issues = volumes_dict[volume_num]
            
            # Get year from first issue's publication date
            year = None
            if volume_issues and volume_issues[0].publication_date:
                year = volume_issues[0].publication_date.year
            
            # Count total articles in this volume
            total_articles = sum(issue.articles.count() for issue in volume_issues)
            
            # Serialize issues
            serializer = IssueWithArticlesSerializer(
                volume_issues, 
                many=True, 
                context={'request': request}
            )
            
            volumes_data.append({
                'volume': volume_num,
                'year': year,
                'issues_count': len(volume_issues),
                'articles_count': total_articles,
                'issues': serializer.data
            })
        
        response_data = {
            'journal_id': journal.id,
            'journal_title': journal.title,
            'total_volumes': len(volumes_data),
            'volumes': volumes_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


# ==================== PUBLIC INSTITUTION VIEWS ====================

class PublicInstitutionsListView(generics.ListAPIView):
    """
    List all institutions publicly (no authentication required).
    Supports comprehensive filtering by country, type, city, research areas, and more.
    """
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        from users.models import Institution
        queryset = Institution.objects.select_related('user', 'stats').prefetch_related('journals')
        
        # Filter by country (exact match, case-insensitive)
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country__iexact=country)
        
        # Filter by institution type
        institution_type = self.request.query_params.get('type', None)
        if institution_type:
            queryset = queryset.filter(institution_type=institution_type)
        
        # Filter by city
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filter by state/province
        state = self.request.query_params.get('state', None)
        if state:
            queryset = queryset.filter(state__icontains=state)
        
        # Filter by established year
        established_year = self.request.query_params.get('established_year', None)
        if established_year:
            try:
                queryset = queryset.filter(established_year=int(established_year))
            except ValueError:
                pass
        
        # Filter by year range
        established_from = self.request.query_params.get('established_from', None)
        established_to = self.request.query_params.get('established_to', None)
        if established_from:
            try:
                queryset = queryset.filter(established_year__gte=int(established_from))
            except ValueError:
                pass
        if established_to:
            try:
                queryset = queryset.filter(established_year__lte=int(established_to))
            except ValueError:
                pass
        
        # Filter by research areas
        research_area = self.request.query_params.get('research_area', None)
        if research_area:
            queryset = queryset.filter(research_areas__icontains=research_area)
        
        # Filter by minimum number of researchers
        min_researchers = self.request.query_params.get('min_researchers', None)
        if min_researchers:
            try:
                queryset = queryset.filter(total_researchers__gte=int(min_researchers))
            except ValueError:
                pass
        
        # Filter by total publications (via stats)
        min_publications = self.request.query_params.get('min_publications', None)
        if min_publications:
            try:
                queryset = queryset.filter(stats__total_publications__gte=int(min_publications))
            except ValueError:
                pass
        
        # Filter by total citations (via stats)
        min_citations = self.request.query_params.get('min_citations', None)
        if min_citations:
            try:
                queryset = queryset.filter(stats__total_citations__gte=int(min_citations))
            except ValueError:
                pass
        
        # Filter by having a website
        has_website = self.request.query_params.get('has_website', None)
        if has_website and has_website.lower() in ['true', '1', 'yes']:
            queryset = queryset.exclude(website='')
        elif has_website and has_website.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(Q(website='') | Q(website__isnull=True))
        
        # Search by name, city, description, or research areas
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(institution_name__icontains=search) |
                Q(city__icontains=search) |
                Q(state__icontains=search) |
                Q(country__icontains=search) |
                Q(description__icontains=search) |
                Q(research_areas__icontains=search)
            )
        
        return queryset.distinct()
    
    def get_serializer_class(self):
        from researchindex.users.serializers.serializers import InstitutionListSerializer
        return InstitutionListSerializer
    
    @extend_schema(
        tags=['Public Institutions'],
        summary='List All Institutions (Public)',
        description='Retrieve all institutions. No authentication required. Supports comprehensive filtering and search.',
        parameters=[
            OpenApiParameter(
                name='country',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by country name (exact match, case-insensitive)',
                required=False,
            ),
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by institution type (university, research_institute, government, private, industry, hospital, other)',
                required=False,
            ),
            OpenApiParameter(
                name='city',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by city name (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='state',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by state/province (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='established_year',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by specific establishment year',
                required=False,
            ),
            OpenApiParameter(
                name='established_from',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter institutions established from this year onwards',
                required=False,
            ),
            OpenApiParameter(
                name='established_to',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter institutions established up to this year',
                required=False,
            ),
            OpenApiParameter(
                name='research_area',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by research area (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='min_researchers',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter institutions with at least this many researchers',
                required=False,
            ),
            OpenApiParameter(
                name='min_publications',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter institutions with at least this many publications',
                required=False,
            ),
            OpenApiParameter(
                name='min_citations',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter institutions with at least this many total citations',
                required=False,
            ),
            OpenApiParameter(
                name='has_website',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by website availability (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in institution name, city, state, country, description, or research areas',
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
        from researchindex.users.serializers.serializers import InstitutionDetailSerializer
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
    Supports comprehensive filtering by institute, designation, title, research interests, and more.
    """
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        from users.models import Author
        queryset = Author.objects.select_related('user', 'stats')
        
        # Filter by title (Dr., Prof., etc.)
        title = self.request.query_params.get('title', None)
        if title:
            queryset = queryset.filter(title=title)
        
        # Filter by institute (partial match)
        institute = self.request.query_params.get('institute', None)
        if institute:
            queryset = queryset.filter(institute__icontains=institute)
        
        # Filter by designation (partial match)
        designation = self.request.query_params.get('designation', None)
        if designation:
            queryset = queryset.filter(designation__icontains=designation)
        
        # Filter by gender
        gender = self.request.query_params.get('gender', None)
        if gender:
            queryset = queryset.filter(gender=gender)
        
        # Filter by degree
        degree = self.request.query_params.get('degree', None)
        if degree:
            queryset = queryset.filter(degree__icontains=degree)
        
        # Filter by research interests
        research_interest = self.request.query_params.get('research_interest', None)
        if research_interest:
            queryset = queryset.filter(research_interests__icontains=research_interest)
        
        # Filter by h-index range
        h_index_min = self.request.query_params.get('h_index_min', None)
        h_index_max = self.request.query_params.get('h_index_max', None)
        if h_index_min:
            try:
                queryset = queryset.filter(stats__h_index__gte=int(h_index_min))
            except ValueError:
                pass
        if h_index_max:
            try:
                queryset = queryset.filter(stats__h_index__lte=int(h_index_max))
            except ValueError:
                pass
        
        # Filter by i10-index range
        i10_index_min = self.request.query_params.get('i10_index_min', None)
        i10_index_max = self.request.query_params.get('i10_index_max', None)
        if i10_index_min:
            try:
                queryset = queryset.filter(stats__i10_index__gte=int(i10_index_min))
            except ValueError:
                pass
        if i10_index_max:
            try:
                queryset = queryset.filter(stats__i10_index__lte=int(i10_index_max))
            except ValueError:
                pass
        
        # Filter by total citations
        min_citations = self.request.query_params.get('min_citations', None)
        max_citations = self.request.query_params.get('max_citations', None)
        if min_citations:
            try:
                queryset = queryset.filter(stats__total_citations__gte=int(min_citations))
            except ValueError:
                pass
        if max_citations:
            try:
                queryset = queryset.filter(stats__total_citations__lte=int(max_citations))
            except ValueError:
                pass
        
        # Filter by total publications
        min_publications = self.request.query_params.get('min_publications', None)
        max_publications = self.request.query_params.get('max_publications', None)
        if min_publications:
            try:
                queryset = queryset.filter(stats__total_publications__gte=int(min_publications))
            except ValueError:
                pass
        if max_publications:
            try:
                queryset = queryset.filter(stats__total_publications__lte=int(max_publications))
            except ValueError:
                pass
        
        # Filter by ORCID presence
        has_orcid = self.request.query_params.get('has_orcid', None)
        if has_orcid and has_orcid.lower() in ['true', '1', 'yes']:
            queryset = queryset.exclude(orcid='')
        elif has_orcid and has_orcid.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(Q(orcid='') | Q(orcid__isnull=True))
        
        # Filter by Google Scholar presence
        has_google_scholar = self.request.query_params.get('has_google_scholar', None)
        if has_google_scholar and has_google_scholar.lower() in ['true', '1', 'yes']:
            queryset = queryset.exclude(google_scholar='')
        elif has_google_scholar and has_google_scholar.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(Q(google_scholar='') | Q(google_scholar__isnull=True))
        
        # Filter by website presence
        has_website = self.request.query_params.get('has_website', None)
        if has_website and has_website.lower() in ['true', '1', 'yes']:
            queryset = queryset.exclude(website='')
        elif has_website and has_website.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(Q(website='') | Q(website__isnull=True))
        
        # Search by name, institute, research interests, or bio
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(institute__icontains=search) |
                Q(designation__icontains=search) |
                Q(degree__icontains=search) |
                Q(research_interests__icontains=search) |
                Q(bio__icontains=search)
            )
        
        return queryset.distinct()
    
    def get_serializer_class(self):
        from researchindex.users.serializers.serializers import AuthorListSerializer
        return AuthorListSerializer
    
    @extend_schema(
        tags=['Public Authors'],
        summary='List All Authors (Public)',
        description='Retrieve all authors. No authentication required. Supports comprehensive filtering and search.',
        parameters=[
            OpenApiParameter(
                name='title',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by title (Dr., Prof., Mr., Ms., Mrs.)',
                required=False,
            ),
            OpenApiParameter(
                name='institute',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by institute name (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='designation',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by designation (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='gender',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by gender (male, female, other, prefer_not_to_say)',
                required=False,
            ),
            OpenApiParameter(
                name='degree',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by highest degree (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='research_interest',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by research interest (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='h_index_min',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter authors with h-index at least this value',
                required=False,
            ),
            OpenApiParameter(
                name='h_index_max',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter authors with h-index at most this value',
                required=False,
            ),
            OpenApiParameter(
                name='i10_index_min',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter authors with i10-index at least this value',
                required=False,
            ),
            OpenApiParameter(
                name='i10_index_max',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter authors with i10-index at most this value',
                required=False,
            ),
            OpenApiParameter(
                name='min_citations',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter authors with at least this many total citations',
                required=False,
            ),
            OpenApiParameter(
                name='max_citations',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter authors with at most this many total citations',
                required=False,
            ),
            OpenApiParameter(
                name='min_publications',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter authors with at least this many publications',
                required=False,
            ),
            OpenApiParameter(
                name='max_publications',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter authors with at most this many publications',
                required=False,
            ),
            OpenApiParameter(
                name='has_orcid',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by ORCID availability (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='has_google_scholar',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by Google Scholar profile availability (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='has_website',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by personal website availability (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in author name, institute, designation, degree, research interests, or bio',
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
        from researchindex.users.serializers.serializers import AuthorDetailSerializer
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


class PublicAuthorPublicationsView(generics.ListAPIView):
    """
    List all publications for a specific author (public access).
    No authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicationListSerializer
    
    def get_queryset(self):
        author_id = self.kwargs.get('author_pk')
        queryset = Publication.objects.filter(
            author_id=author_id,
            is_published=True
        ).select_related(
            'author__user', 'journal', 'topic_branch__topic', 'stats'
        ).prefetch_related(
            'mesh_terms', 'citations', 'references', 'link_outs'
        ).order_by('-published_date')
        
        # Filter by publication type
        pub_type = self.request.query_params.get('type', None)
        if pub_type:
            queryset = queryset.filter(publication_type=pub_type)
        
        # Filter by topic branch
        topic_branch = self.request.query_params.get('topic_branch', None)
        if topic_branch:
            queryset = queryset.filter(topic_branch_id=topic_branch)
        
        # Search by title or abstract
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(abstract__icontains=search)
            )
        
        return queryset
    
    @extend_schema(
        tags=['Public Authors'],
        summary='List Author Publications (Public)',
        description='Retrieve all publications for a specific author. No authentication required.',
        parameters=[
            OpenApiParameter(
                name='author_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Author ID',
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
                name='topic_branch',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by topic branch ID',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title or abstract',
                required=False,
            ),
        ],
        responses={200: PublicationListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicInstitutionPublicationsView(generics.ListAPIView):
    """
    List all publications for authors from a specific institution (public access).
    No authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicationListSerializer
    
    def get_queryset(self):
        institution_id = self.kwargs.get('institution_pk')
        
        # Get institution details
        from users.models import Institution
        try:
            institution = Institution.objects.get(id=institution_id)
            institution_name = institution.institution_name
        except Institution.DoesNotExist:
            return Publication.objects.none()
        
        # Get all authors from this institution (match by institution name in institute field)
        from users.models import Author
        author_ids = Author.objects.filter(
            institute__icontains=institution_name
        ).values_list('id', flat=True)
        
        queryset = Publication.objects.filter(
            author_id__in=author_ids,
            is_published=True
        ).select_related(
            'author__user', 'journal', 'topic_branch__topic', 'stats'
        ).prefetch_related(
            'mesh_terms', 'citations', 'references', 'link_outs'
        ).order_by('-published_date')
        
        # Filter by publication type
        pub_type = self.request.query_params.get('type', None)
        if pub_type:
            queryset = queryset.filter(publication_type=pub_type)
        
        # Filter by topic branch
        topic_branch = self.request.query_params.get('topic_branch', None)
        if topic_branch:
            queryset = queryset.filter(topic_branch_id=topic_branch)
        
        # Search by title or abstract
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(abstract__icontains=search) |
                Q(author__full_name__icontains=search)
            )
        
        return queryset
    
    @extend_schema(
        tags=['Public Institutions'],
        summary='List Institution Publications (Public)',
        description='Retrieve all publications from authors belonging to a specific institution. No authentication required.',
        parameters=[
            OpenApiParameter(
                name='institution_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Institution ID',
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
                name='topic_branch',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by topic branch ID',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, abstract, or author name',
                required=False,
            ),
        ],
        responses={200: PublicationListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ==================== DOAJ API VIEWS ====================

class DOAJSearchView(APIView):
    """
    Search journals in DOAJ (Directory of Open Access Journals)
    Requires authentication
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['DOAJ'],
        summary='Search DOAJ Journals',
        description='Search for journals in the Directory of Open Access Journals (DOAJ) by title, ISSN, or keywords.',
        parameters=[
            OpenApiParameter(
                name='q',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search query (journal title, ISSN, keywords)',
                required=True,
            ),
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number (default: 1)',
                required=False,
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Results per page (default: 10, max: 100)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Search results from DOAJ',
                response={
                    'type': 'object',
                    'properties': {
                        'total': {'type': 'integer'},
                        'page': {'type': 'integer'},
                        'page_size': {'type': 'integer'},
                        'results': {'type': 'array'},
                    }
                }
            ),
            400: OpenApiResponse(description='Missing query parameter'),
            500: OpenApiResponse(description='DOAJ API error'),
        }
    )
    def get(self, request):
        from ..doaj_api import DOAJAPI, DOAJAPIError
        
        query = request.query_params.get('q')
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 10)), 100)
        
        try:
            results = DOAJAPI.search_journals(query, page, page_size)
            return Response(results, status=status.HTTP_200_OK)
        except DOAJAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DOAJJournalByISSNView(APIView):
    """
    Get journal details from DOAJ by ISSN
    Requires authentication
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['DOAJ'],
        summary='Get DOAJ Journal by ISSN',
        description='Retrieve journal details from DOAJ using ISSN (print or electronic).',
        parameters=[
            OpenApiParameter(
                name='issn',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Journal ISSN (with or without hyphen)',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Journal details from DOAJ'),
            404: OpenApiResponse(description='Journal not found in DOAJ'),
            500: OpenApiResponse(description='DOAJ API error'),
        }
    )
    def get(self, request, issn):
        from ..doaj_api import DOAJAPI, DOAJAPIError
        
        try:
            journal = DOAJAPI.get_journal_by_issn(issn)
            if journal:
                return Response(journal, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f'Journal with ISSN {issn} not found in DOAJ'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except DOAJAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


from django.views import View

class ExportJournalView(View):
    """
    Export journal details in various formats (JSON, CSV, PDF).
    Public endpoint - no authentication required.
    Uses regular Django View to bypass DRF content negotiation.
    """
    
    def get(self, request, pk):
        import csv
        import json
        from django.http import HttpResponse, JsonResponse
        from io import StringIO
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get the journal (only active journals)
        try:
            journal = Journal.objects.select_related('institution').prefetch_related('editorial_board').filter(
                is_active=True
            ).get(pk=pk)
        except Journal.DoesNotExist:
            return JsonResponse({'error': 'Journal not found'}, status=404)
        
        # Get export format from query params (default: json)
        export_format = request.GET.get('format', 'json').lower()
        logger.info(f"Export request for journal {pk}, format: {export_format}")
        
        # Create safe filename
        import re
        safe_title = journal.short_title or journal.title
        safe_filename = re.sub(r'[^\w\s-]', '', safe_title)[:50]  # Remove special chars, limit length
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename)  # Replace spaces/hyphens with underscore
        safe_filename = safe_filename.strip('_') or f'journal_{journal.id}'  # Fallback to ID if empty
        
        # Prepare journal data
        journal_data = {
            'id': journal.id,
            'title': journal.title,
            'short_title': journal.short_title,
            'issn': journal.issn,
            'e_issn': journal.e_issn,
            'doi_prefix': journal.doi_prefix,
            'description': journal.description,
            'scope': journal.scope,
            'institution_name': journal.institution.institution_name if journal.institution else '',
            'publisher_name': journal.publisher_name,
            'frequency': journal.get_frequency_display(),
            'established_year': journal.established_year,
            'is_open_access': journal.is_open_access,
            'peer_reviewed': journal.peer_reviewed,
            'language': journal.language,
            'contact_email': journal.contact_email,
            'contact_phone': journal.contact_phone,
            'contact_address': journal.contact_address,
            'website': journal.website,
        }
        
        # Add stats if available
        if hasattr(journal, 'stats'):
            journal_data.update({
                'total_publications': journal.stats.total_publications,
                'total_issues': journal.stats.total_issues,
                'total_citations': journal.stats.total_citations,
                'impact_factor': str(journal.stats.impact_factor) if journal.stats.impact_factor else None,
                'h_index': journal.stats.h_index,
            })
        
        # Handle different export formats
        if export_format == 'json':
            response = JsonResponse(journal_data, json_dumps_params={'indent': 2})
            response['Content-Disposition'] = f'attachment; filename="{safe_filename}.json"'
            return response
            
        elif export_format == 'csv':
            # Create CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers and values
            writer.writerow(['Field', 'Value'])
            for key, value in journal_data.items():
                writer.writerow([key, value])
            
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{safe_filename}.csv"'
            return response
            
        elif export_format == 'pdf':
            # Generate actual PDF using reportlab
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)
            
            # Container for PDF elements
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#333333'),
                spaceAfter=12,
            )
            
            normal_style = styles['Normal']
            
            # Add title
            elements.append(Paragraph("JOURNAL EXPORT REPORT", title_style))
            elements.append(Spacer(1, 0.2 * inch))
            
            # Basic Information
            elements.append(Paragraph("Basic Information", heading_style))
            basic_data = [
                ['Title:', journal.title or 'N/A'],
                ['Short Title:', journal.short_title or 'N/A'],
                ['ISSN:', journal.issn or 'N/A'],
                ['E-ISSN:', journal.e_issn or 'N/A'],
                ['DOI Prefix:', journal.doi_prefix or 'N/A'],
                ['Institution:', journal.institution.institution_name if journal.institution else 'N/A'],
                ['Publisher:', journal.publisher_name or 'N/A'],
                ['Frequency:', journal.get_frequency_display()],
                ['Established Year:', str(journal.established_year) if journal.established_year else 'N/A'],
            ]
            basic_table = Table(basic_data, colWidths=[2*inch, 4*inch])
            basic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(basic_table)
            elements.append(Spacer(1, 0.3 * inch))
            
            # Access & Review Information
            elements.append(Paragraph("Access & Review Information", heading_style))
            access_data = [
                ['Open Access:', 'Yes' if journal.is_open_access else 'No'],
                ['Peer Reviewed:', 'Yes' if journal.peer_reviewed else 'No'],
                ['Language:', journal.language or 'N/A'],
            ]
            access_table = Table(access_data, colWidths=[2*inch, 4*inch])
            access_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(access_table)
            elements.append(Spacer(1, 0.3 * inch))
            
            # Contact Information
            elements.append(Paragraph("Contact Information", heading_style))
            contact_data = [
                ['Email:', journal.contact_email or 'N/A'],
                ['Phone:', journal.contact_phone or 'N/A'],
                ['Address:', journal.contact_address or 'N/A'],
                ['Website:', journal.website or 'N/A'],
            ]
            contact_table = Table(contact_data, colWidths=[2*inch, 4*inch])
            contact_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(contact_table)
            elements.append(Spacer(1, 0.3 * inch))
            
            # Statistics
            elements.append(Paragraph("Statistics", heading_style))
            stats_data = [
                ['Total Publications:', str(journal.stats.total_publications) if hasattr(journal, 'stats') else 'N/A'],
                ['Total Issues:', str(journal.stats.total_issues) if hasattr(journal, 'stats') else 'N/A'],
                ['Total Citations:', str(journal.stats.total_citations) if hasattr(journal, 'stats') else 'N/A'],
                ['Impact Factor:', str(journal.stats.impact_factor) if hasattr(journal, 'stats') else 'N/A'],
                ['H-Index:', str(journal.stats.h_index) if hasattr(journal, 'stats') else 'N/A'],
            ]
            stats_table = Table(stats_data, colWidths=[2*inch, 4*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 0.3 * inch))
            
            # Description
            if journal.description:
                elements.append(Paragraph("Description", heading_style))
                # Escape HTML characters and handle line breaks
                desc_text = journal.description.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                desc_text = desc_text.replace('\n', '<br/>')
                elements.append(Paragraph(desc_text, normal_style))
                elements.append(Spacer(1, 0.3 * inch))
            
            # Scope
            if journal.scope:
                elements.append(Paragraph("Scope", heading_style))
                scope_text = journal.scope.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                scope_text = scope_text.replace('\n', '<br/>')
                elements.append(Paragraph(scope_text, normal_style))
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF data
            pdf_data = buffer.getvalue()
            buffer.close()
            
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{safe_filename}.pdf"'
            return response
        else:
            return JsonResponse(
                {'error': 'Invalid format. Supported formats: json, csv, pdf'},
                status=400
            )


class ShareJournalView(APIView):
    """
    Generate shareable link and metadata for journal.
    Public endpoint - no authentication required.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Journals'],
        summary='Get Journal Share Information',
        description='Get shareable link and metadata for social media sharing.',
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Journal ID',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Share information including URL and metadata'),
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def get(self, request, pk):
        # Get the journal (only active journals)
        try:
            journal = Journal.objects.select_related('institution', 'stats').filter(
                is_active=True
            ).get(pk=pk)
        except Journal.DoesNotExist:
            return Response({'error': 'Journal not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Build the full URL for sharing (pointing to frontend)
        from django.conf import settings
        frontend_base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        frontend_url = f"{frontend_base_url}/journals/{pk}"
        
        # Get cover image URL if available
        cover_image_url = None
        if journal.cover_image:
            try:
                cover_image_url = request.build_absolute_uri(journal.cover_image.url)
            except Exception:
                cover_image_url = None
        
        # Prepare share data
        share_data = {
            'url': frontend_url,
            'title': journal.title,
            'description': journal.description[:200] if journal.description else f"Explore {journal.title} - {journal.institution.institution_name if journal.institution else 'Journal'}",
            'image': cover_image_url,
            'metadata': {
                'issn': journal.issn,
                'e_issn': journal.e_issn,
                'publisher': journal.publisher_name,
                'institution': journal.institution.institution_name if journal.institution else None,
                'is_open_access': journal.is_open_access,
                'impact_factor': str(journal.stats.impact_factor) if hasattr(journal, 'stats') and journal.stats.impact_factor else None,
            },
            'social_share_urls': {
                'twitter': f"https://twitter.com/intent/tweet?url={frontend_url}&text={journal.title}",
                'facebook': f"https://www.facebook.com/sharer/sharer.php?u={frontend_url}",
                'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={frontend_url}",
                'whatsapp': f"https://wa.me/?text={journal.title}%20{frontend_url}",
                'email': f"mailto:?subject={journal.title}&body=Check out this journal: {frontend_url}",
            }
        }
        
        return Response(share_data, status=status.HTTP_200_OK)


# ==================== ADMIN ENDPOINTS ====================

class SyncCitationsAdminView(APIView):
    """
    Admin endpoint to sync citation counts from Crossref API.
    
    Fetches citation counts for publications with DOIs from the Crossref API
    and updates the PublicationStats.citations_count field.
    """
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        tags=['Admin'],
        summary='Sync Citations from Crossref (Admin)',
        description='Sync citation counts from Crossref API for publications with DOIs. Admin only.',
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                description='Limit number of publications to sync',
                required=False,
            ),
            OpenApiParameter(
                name='journal_id',
                type=int,
                description='Sync citations only for publications in a specific journal',
                required=False,
            ),
            OpenApiParameter(
                name='force',
                type=bool,
                description='Force re-sync even if recently updated (within 7 days)',
                required=False,
            ),
            OpenApiParameter(
                name='delay',
                type=float,
                description='Delay between API requests in seconds (default: 0.1)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Citation sync completed',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'total_processed': {'type': 'integer'},
                        'success_count': {'type': 'integer'},
                        'updated_count': {'type': 'integer'},
                        'unchanged_count': {'type': 'integer'},
                        'error_count': {'type': 'integer'},
                        'details': {'type': 'array'},
                    }
                }
            ),
            403: OpenApiResponse(description='Admin permission required'),
        }
    )
    def post(self, request):
        # Get query parameters
        limit = request.query_params.get('limit')
        journal_id = request.query_params.get('journal_id')
        force = request.query_params.get('force', 'false').lower() == 'true'
        delay = float(request.query_params.get('delay', 0.1))
        
        if limit:
            limit = int(limit)
        if journal_id:
            journal_id = int(journal_id)
        
        # Build query
        query = Publication.objects.filter(
            is_published=True,
            doi__isnull=False
        ).exclude(doi='').select_related('stats', 'journal')
        
        if journal_id:
            query = query.filter(journal_id=journal_id)
        
        # Skip recently updated unless forced
        if not force:
            cutoff_date = timezone.now() - timedelta(days=7)
            query = query.exclude(stats__last_updated__gte=cutoff_date)
        
        if limit:
            query = query[:limit]
        
        publications = list(query)
        total = len(publications)
        
        if total == 0:
            return Response({
                'message': 'No publications found to sync',
                'total_processed': 0,
                'success_count': 0,
                'error_count': 0,
            }, status=status.HTTP_200_OK)
        
        # Initialize Crossref API
        api = CrossrefCitationAPI()
        
        # Process publications
        success_count = 0
        error_count = 0
        updated_count = 0
        unchanged_count = 0
        details = []
        
        for idx, publication in enumerate(publications, 1):
            try:
                # Fetch citation count from Crossref
                citation_count = api.get_citation_count(publication.doi)
                
                if citation_count is not None:
                    # Get or create stats
                    stats, created = PublicationStats.objects.get_or_create(
                        publication=publication
                    )
                    
                    old_count = stats.citations_count
                    
                    # Update citation count
                    stats.citations_count = citation_count
                    stats.save()
                    
                    success_count += 1
                    
                    if old_count != citation_count:
                        updated_count += 1
                        details.append({
                            'id': publication.id,
                            'title': publication.title[:60],
                            'doi': publication.doi,
                            'old_citations': old_count,
                            'new_citations': citation_count,
                            'status': 'updated'
                        })
                    else:
                        unchanged_count += 1
                        details.append({
                            'id': publication.id,
                            'title': publication.title[:60],
                            'doi': publication.doi,
                            'citations': citation_count,
                            'status': 'unchanged'
                        })
                else:
                    error_count += 1
                    details.append({
                        'id': publication.id,
                        'title': publication.title[:60],
                        'doi': publication.doi,
                        'status': 'error',
                        'error': 'Could not fetch citation count'
                    })
                
                # Delay to respect rate limits
                if idx < total:
                    time.sleep(delay)
                    
            except Exception as e:
                error_count += 1
                details.append({
                    'id': publication.id,
                    'title': publication.title[:60],
                    'doi': publication.doi,
                    'status': 'error',
                    'error': str(e)
                })
                logger.exception(f"Error syncing citations for publication {publication.id}")
        
        return Response({
            'message': 'Citation sync completed',
            'total_processed': total,
            'success_count': success_count,
            'updated_count': updated_count,
            'unchanged_count': unchanged_count,
            'error_count': error_count,
            'details': details,
            'tip': 'Run recalculate-stats endpoint to update journal metrics based on new citation data'
        }, status=status.HTTP_200_OK)


class RecalculateStatsAdminView(APIView):
    """
    Admin endpoint to recalculate statistics for journals.
    
    Recalculates h-index, impact factor, cite score, total citations, reads,
    and other metrics based on current publications data.
    """
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        tags=['Admin'],
        summary='Recalculate Journal Statistics (Admin)',
        description='Recalculate statistics for all journals or a specific journal. Admin only.',
        parameters=[
            OpenApiParameter(
                name='journal_id',
                type=int,
                description='Recalculate stats for a specific journal ID',
                required=False,
            ),
            OpenApiParameter(
                name='create_missing',
                type=bool,
                description='Create JournalStats for journals that don\'t have them (default: true)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Stats recalculation completed',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'total_journals': {'type': 'integer'},
                        'success_count': {'type': 'integer'},
                        'created_count': {'type': 'integer'},
                        'error_count': {'type': 'integer'},
                        'details': {'type': 'array'},
                    }
                }
            ),
            404: OpenApiResponse(description='Journal not found'),
            403: OpenApiResponse(description='Admin permission required'),
        }
    )
    def post(self, request):
        # Get query parameters
        journal_id = request.query_params.get('journal_id')
        create_missing = request.query_params.get('create_missing', 'true').lower() == 'true'
        
        if journal_id:
            journal_id = int(journal_id)
        
        if journal_id:
            # Recalculate for specific journal
            try:
                journal = Journal.objects.get(id=journal_id)
                stats, created = JournalStats.objects.get_or_create(journal=journal)
                stats.update_stats()
                
                return Response({
                    'message': f'Successfully recalculated stats for journal: {journal.title}',
                    'journal': {
                        'id': journal.id,
                        'title': journal.title,
                        'total_articles': stats.total_articles,
                        'total_issues': stats.total_issues,
                        'total_citations': stats.total_citations,
                        'impact_factor': str(stats.impact_factor) if stats.impact_factor else None,
                        'cite_score': str(stats.cite_score) if stats.cite_score else None,
                        'h_index': stats.h_index,
                    },
                    'created': created,
                }, status=status.HTTP_200_OK)
            except Journal.DoesNotExist:
                return Response({
                    'error': f'Journal with ID {journal_id} does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Recalculate for all journals
            journals = Journal.objects.all()
            total_journals = journals.count()
            
            success_count = 0
            created_count = 0
            error_count = 0
            details = []
            
            for journal in journals:
                try:
                    # Create stats if missing
                    stats, created = JournalStats.objects.get_or_create(journal=journal)
                    if created:
                        created_count += 1
                    
                    # Recalculate stats
                    stats.update_stats()
                    success_count += 1
                    
                    details.append({
                        'id': journal.id,
                        'title': journal.title,
                        'total_articles': stats.total_articles,
                        'total_issues': stats.total_issues,
                        'total_citations': stats.total_citations,
                        'impact_factor': str(stats.impact_factor) if stats.impact_factor else None,
                        'cite_score': str(stats.cite_score) if stats.cite_score else None,
                        'h_index': stats.h_index,
                        'created': created,
                    })
                except Exception as e:
                    error_count += 1
                    details.append({
                        'id': journal.id,
                        'title': journal.title,
                        'status': 'error',
                        'error': str(e)
                    })
                    logger.exception(f"Error recalculating stats for journal {journal.id}")
            
            return Response({
                'message': 'Stats recalculation completed',
                'total_journals': total_journals,
                'success_count': success_count,
                'created_count': created_count,
                'error_count': error_count,
                'details': details,
            }, status=status.HTTP_200_OK)
