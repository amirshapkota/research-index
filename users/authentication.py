"""
Custom authentication class for JWT tokens stored in HTTP-only cookies.

This provides enhanced security by storing tokens in HTTP-only cookies
instead of localStorage, protecting against XSS attacks.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework import exceptions
from django.conf import settings


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom authentication class that extracts JWT tokens from HTTP-only cookies.
    
    Falls back to Authorization header if cookie is not present,
    maintaining backward compatibility.
    """
    
    def authenticate(self, request):
        """
        Try to authenticate the request using JWT token from cookie or header.
        
        Priority:
        1. HTTP-only cookie (most secure)
        2. Authorization header (backward compatibility)
        """
        # Try to get token from cookie first
        cookie_name = getattr(settings, 'JWT_AUTH_COOKIE', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)
        
        if raw_token is None:
            # Fallback to Authorization header
            header = self.get_header(request)
            if header is None:
                return None
            
            raw_token = self.get_raw_token(header)
        
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken as e:
            raise exceptions.AuthenticationFailed('Invalid token') from e


class JWTRefreshCookieAuthentication(JWTAuthentication):
    """
    Authentication class for refresh tokens stored in HTTP-only cookies.
    Used specifically for token refresh endpoint.
    """
    
    def authenticate(self, request):
        """
        Authenticate using refresh token from cookie.
        """
        cookie_name = getattr(settings, 'JWT_REFRESH_COOKIE', 'refresh_token')
        raw_token = request.COOKIES.get(cookie_name)
        
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken as e:
            raise exceptions.AuthenticationFailed('Invalid refresh token') from e
