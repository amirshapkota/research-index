from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportPageViewSet, SponsorViewSet

router = DefaultRouter()
router.register(r'pages', SupportPageViewSet, basename='support-pages')
router.register(r'sponsors', SponsorViewSet, basename='sponsors')

urlpatterns = [
    path('', include(router.urls)),
]
