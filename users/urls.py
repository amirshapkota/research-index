from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    AuthorRegistrationView,
    InstitutionRegistrationView,
    LoginView,
    AuthorProfileView,
    InstitutionProfileView
)

urlpatterns = [
    # Registration endpoints
    path('register/author/', AuthorRegistrationView.as_view(), name='author-register'),
    path('register/institution/', InstitutionRegistrationView.as_view(), name='institution-register'),
    
    # Login endpoint
    path('login/', LoginView.as_view(), name='login'),
    
    # Token refresh endpoint
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Profile endpoints
    path('profile/author/', AuthorProfileView.as_view(), name='author-profile'),
    path('profile/institution/', InstitutionProfileView.as_view(), name='institution-profile'),
]