from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.core.mail import send_mail
from django.conf import settings
from urllib.parse import unquote
from .models import Contact
from .serializers import ContactSerializer
from .services.crossref import CrossrefService


class ContactCreateView(generics.CreateAPIView):
    """
    Submit a contact enquiry form.
    
    Anyone can submit a contact form without authentication.
    An email notification will be sent to admins upon submission.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Contact'],
        summary='Submit Contact Form',
        description='Submit a contact enquiry. No authentication required. An email notification will be sent upon successful submission.',
        examples=[
            OpenApiExample(
                'Contact Form Example',
                value={
                    'full_name': 'John Doe',
                    'email': 'john.doe@example.com',
                    'contact_number': '+1-234-567-8900',
                    'institution_name': 'MIT',
                    'enquiry_type': 'general',
                    'subject': 'Question about research collaboration',
                    'message': 'I would like to know more about potential research collaboration opportunities...'
                },
                request_only=True,
            )
        ],
        responses={
            201: OpenApiResponse(
                description='Contact enquiry submitted successfully',
                response=ContactSerializer,
            ),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        
        # Send email notification
        self.send_email_notification(contact)
        
        return Response({
            'message': 'Your enquiry has been submitted successfully. We will get back to you soon.',
            'contact': ContactSerializer(contact).data
        }, status=status.HTTP_201_CREATED)
    
    def send_email_notification(self, contact):
        """Send email notification to admin and confirmation to user"""
        try:
            # Email to admin
            admin_subject = f'New Contact Enquiry: {contact.subject}'
            admin_message = f"""
New contact enquiry received:

Name: {contact.full_name}
Email: {contact.email}
Contact Number: {contact.contact_number}
Institution: {contact.institution_name}
Enquiry Type: {contact.get_enquiry_type_display()}
Subject: {contact.subject}

Message:
{contact.message}

---
Submitted at: {contact.created_at.strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            send_mail(
                subject=admin_subject,
                message=admin_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
            
            # Confirmation email to user
            user_subject = f'We received your enquiry: {contact.subject}'
            user_message = f"""
Dear {contact.full_name},

Thank you for contacting Research Index. We have received your enquiry regarding "{contact.subject}".

Our team will review your message and get back to you as soon as possible.

Your Enquiry Details:
- Subject: {contact.subject}
- Enquiry Type: {contact.get_enquiry_type_display()}
- Submitted: {contact.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
Research Index Team
            """
            
            send_mail(
                subject=user_subject,
                message=user_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error sending email: {str(e)}")


# ==================== CROSSREF API VIEWS ====================

class CrossrefWorkByDOIView(APIView):
    """
    Retrieve publication metadata from Crossref by DOI.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Get Work by DOI',
        description='Retrieve complete metadata for a publication using its DOI from Crossref API.',
        parameters=[
            OpenApiParameter(
                name='doi',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Digital Object Identifier (e.g., 10.1037/0003-066X.59.1.29)',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Work metadata retrieved successfully'),
            404: OpenApiResponse(description='DOI not found'),
            500: OpenApiResponse(description='Crossref API error'),
        }
    )
    def get(self, request, doi=None):
        # Accept DOI from either query parameter or path parameter
        if not doi:
            doi = request.query_params.get('doi')
        
        if not doi:
            return Response({
                'status': 'error',
                'message': 'DOI parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # URL-decode the DOI (handles encoded slashes like %2F)
        doi = unquote(doi)
        service = CrossrefService()
        work = service.get_work_by_doi(doi)
        
        if work:
            # Extract normalized data for easier consumption
            normalized_data = service.extract_publication_data(work)
            
            return Response({
                'status': 'success',
                'data': {
                    'raw': work,  # Full Crossref response
                    'normalized': normalized_data,  # Processed data
                }
            })
        
        return Response({
            'status': 'error',
            'message': 'DOI not found or Crossref API error'
        }, status=status.HTTP_404_NOT_FOUND)


class CrossrefSearchWorksView(APIView):
    """
    Search for works in Crossref database.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Search Works',
        description='Search for publications in Crossref database using a query string.',
        parameters=[
            OpenApiParameter(
                name='query',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search query (e.g., "climate change machine learning")',
                required=True,
            ),
            OpenApiParameter(
                name='rows',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of results to return (max 1000, default 20)',
                required=False,
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Starting position (default 0)',
                required=False,
            ),
            OpenApiParameter(
                name='sort',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Sort field (e.g., "published", "relevance")',
                required=False,
            ),
            OpenApiParameter(
                name='order',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Sort order: "asc" or "desc" (default desc)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Search results'),
            400: OpenApiResponse(description='Missing query parameter'),
        }
    )
    def get(self, request):
        query = request.query_params.get('query')
        if not query:
            return Response({
                'status': 'error',
                'message': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        rows = int(request.query_params.get('rows', 20))
        offset = int(request.query_params.get('offset', 0))
        sort_field = request.query_params.get('sort')
        order = request.query_params.get('order', 'desc')
        
        service = CrossrefService()
        results = service.search_works(
            query=query,
            rows=rows,
            offset=offset,
            sort=sort_field,
            order=order
        )
        
        if results:
            return Response({
                'status': 'success',
                'data': results
            })
        
        return Response({
            'status': 'error',
            'message': 'Search failed or no results found'
        }, status=status.HTTP_404_NOT_FOUND)


class CrossrefWorkReferencesView(APIView):
    """
    Get references cited by a work.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Get Work References',
        description='Retrieve the list of references cited by a publication.',
        parameters=[
            OpenApiParameter(
                name='doi',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Digital Object Identifier',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description='References retrieved successfully'),
            404: OpenApiResponse(description='DOI not found'),
        }
    )
    def get(self, request, doi=None):
        # Accept DOI from either query parameter or path parameter
        if not doi:
            doi = request.query_params.get('doi')
        
        if not doi:
            return Response({
                'status': 'error',
                'message': 'DOI parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # URL-decode the DOI (handles encoded slashes like %2F)
        doi = unquote(doi)
        service = CrossrefService()
        references = service.get_work_references(doi)
        
        return Response({
            'status': 'success',
            'data': {
                'doi': doi,
                'reference_count': len(references),
                'references': references
            }
        })


class CrossrefWorkCitationsView(APIView):
    """
    Get citation count for a work.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Get Work Citations',
        description='Retrieve citation count and information for a publication.',
        parameters=[
            OpenApiParameter(
                name='doi',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Digital Object Identifier',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Citation information retrieved'),
            404: OpenApiResponse(description='DOI not found'),
        }
    )
    def get(self, request, doi=None):
        # Accept DOI from either query parameter or path parameter
        if not doi:
            doi = request.query_params.get('doi')
        
        if not doi:
            return Response({
                'status': 'error',
                'message': 'DOI parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # URL-decode the DOI (handles encoded slashes like %2F)
        doi = unquote(doi)
        service = CrossrefService()
        citation_info = service.get_work_citations(doi)
        
        if citation_info:
            return Response({
                'status': 'success',
                'data': citation_info
            })
        
        return Response({
            'status': 'error',
            'message': 'DOI not found'
        }, status=status.HTTP_404_NOT_FOUND)


class CrossrefJournalByISSNView(APIView):
    """
    Get journal metadata by ISSN.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Get Journal by ISSN',
        description='Retrieve journal metadata using ISSN.',
        parameters=[
            OpenApiParameter(
                name='issn',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='International Standard Serial Number (e.g., 1476-4687)',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Journal metadata retrieved'),
            404: OpenApiResponse(description='ISSN not found'),
        }
    )
    def get(self, request, issn):
        service = CrossrefService()
        journal = service.get_journal_by_issn(issn)
        
        if journal:
            return Response({
                'status': 'success',
                'data': journal
            })
        
        return Response({
            'status': 'error',
            'message': 'Journal not found'
        }, status=status.HTTP_404_NOT_FOUND)


class CrossrefJournalWorksView(APIView):
    """
    Get works published in a journal.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Get Journal Works',
        description='Retrieve publications from a specific journal by ISSN.',
        parameters=[
            OpenApiParameter(
                name='issn',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='International Standard Serial Number',
                required=True,
            ),
            OpenApiParameter(
                name='rows',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of results (default 20)',
                required=False,
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Starting position (default 0)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Journal works retrieved'),
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def get(self, request, issn):
        rows = int(request.query_params.get('rows', 20))
        offset = int(request.query_params.get('offset', 0))
        
        service = CrossrefService()
        works = service.get_journal_works(issn, rows=rows, offset=offset)
        
        if works:
            return Response({
                'status': 'success',
                'data': works
            })
        
        return Response({
            'status': 'error',
            'message': 'Journal not found or no works available'
        }, status=status.HTTP_404_NOT_FOUND)


class CrossrefValidateDOIView(APIView):
    """
    Validate if a DOI exists in Crossref.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Validate DOI',
        description='Check if a DOI exists and is valid in Crossref database.',
        parameters=[
            OpenApiParameter(
                name='doi',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Digital Object Identifier to validate',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Validation result'),
        }
    )
    def get(self, request):
        doi = request.query_params.get('doi')
        if not doi:
            return Response({
                'status': 'error',
                'message': 'DOI parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = CrossrefService()
        is_valid = service.validate_doi(doi)
        
        return Response({
            'status': 'success',
            'data': {
                'doi': doi,
                'is_valid': is_valid
            }
        })


class CrossrefSearchFundersView(APIView):
    """
    Search for research funders.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Search Funders',
        description='Search for research funding organizations in Crossref database.',
        parameters=[
            OpenApiParameter(
                name='query',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search query (e.g., "National Science Foundation")',
                required=True,
            ),
            OpenApiParameter(
                name='rows',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of results (default 20)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Funder search results'),
            400: OpenApiResponse(description='Missing query parameter'),
        }
    )
    def get(self, request):
        query = request.query_params.get('query')
        if not query:
            return Response({
                'status': 'error',
                'message': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        rows = int(request.query_params.get('rows', 20))
        
        service = CrossrefService()
        results = service.search_funders(query, rows=rows)
        
        if results:
            return Response({
                'status': 'success',
                'data': results
            })
        
        return Response({
            'status': 'error',
            'message': 'Search failed or no results found'
        }, status=status.HTTP_404_NOT_FOUND)
