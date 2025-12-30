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
    Citation, Reference, LinkOut, PublicationRead
)
from .serializers import (
    PublicationListSerializer, PublicationDetailSerializer,
    PublicationCreateUpdateSerializer, AddCitationSerializer,
    AddReferenceSerializer, BulkReferencesSerializer,
    MeSHTermSerializer, LinkOutSerializer, PublicationStatsSerializer
)
from users.models import Author


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
