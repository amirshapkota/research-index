from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import Contact
from .serializers import ContactSerializer


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


