from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ...serializers.serializers import (
    FollowSerializer,
    FollowCreateSerializer,
    FollowerListSerializer,
    FollowingListSerializer,
    FollowStatsSerializer,
)
from ...models import CustomUser, Follow


class FollowUserView(APIView):
    """Follow a user (author or institution)."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Follow'],
        summary='Follow a User',
        description='Follow another user (author or institution). Cannot follow yourself or someone you already follow.',
        request=FollowCreateSerializer,
        responses={
            201: FollowSerializer,
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def post(self, request):
        serializer = FollowCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        follow = serializer.save()
        
        response_serializer = FollowSerializer(follow, context={'request': request})
        return Response({
            'message': 'Successfully followed user',
            'follow': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class UnfollowUserView(APIView):
    """Unfollow a user."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Follow'],
        summary='Unfollow a User',
        description='Unfollow a user you are currently following.',
        responses={
            200: OpenApiResponse(description='Successfully unfollowed'),
            404: OpenApiResponse(description='Not following this user'),
        }
    )
    def delete(self, request, user_id):
        try:
            following_user = CustomUser.objects.get(id=user_id)
            follow = Follow.objects.get(follower=request.user, following=following_user)
            follow.delete()
            
            return Response({
                'message': 'Successfully unfollowed user'
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Follow.DoesNotExist:
            return Response({
                'error': 'You are not following this user'
            }, status=status.HTTP_404_NOT_FOUND)


class MyFollowersView(generics.ListAPIView):
    """List all followers of the current user."""
    permission_classes = [IsAuthenticated]
    serializer_class = FollowerListSerializer
    
    def get_queryset(self):
        return Follow.objects.filter(following=self.request.user).select_related(
            'follower', 'follower__author_profile', 'follower__institution_profile'
        )
    
    @extend_schema(
        tags=['Follow'],
        summary='My Followers',
        description='Get a list of all users following you.',
        responses={200: FollowerListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MyFollowingView(generics.ListAPIView):
    """List all users the current user is following."""
    permission_classes = [IsAuthenticated]
    serializer_class = FollowingListSerializer
    
    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user).select_related(
            'following', 'following__author_profile', 'following__institution_profile'
        )
    
    @extend_schema(
        tags=['Follow'],
        summary='Users I Follow',
        description='Get a list of all users you are following.',
        responses={200: FollowingListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserFollowersView(generics.ListAPIView):
    """List followers of a specific user."""
    permission_classes = [IsAuthenticated]
    serializer_class = FollowerListSerializer
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Follow.objects.filter(following_id=user_id).select_related(
            'follower', 'follower__author_profile', 'follower__institution_profile'
        )
    
    @extend_schema(
        tags=['Follow'],
        summary='User Followers',
        description='Get a list of users following a specific user.',
        responses={200: FollowerListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserFollowingView(generics.ListAPIView):
    """List users that a specific user is following."""
    permission_classes = [IsAuthenticated]
    serializer_class = FollowingListSerializer
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Follow.objects.filter(follower_id=user_id).select_related(
            'following', 'following__author_profile', 'following__institution_profile'
        )
    
    @extend_schema(
        tags=['Follow'],
        summary='Users Being Followed',
        description='Get a list of users that a specific user is following.',
        responses={200: FollowingListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class FollowStatsView(APIView):
    """Get follow statistics for a user."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Follow'],
        summary='Follow Statistics',
        description='Get follower/following counts and check if current user is following the specified user.',
        responses={200: FollowStatsSerializer}
    )
    def get(self, request, user_id=None):
        # If no user_id provided, use current user
        if user_id is None:
            target_user = request.user
        else:
            try:
                target_user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        followers_count = Follow.objects.filter(following=target_user).count()
        following_count = Follow.objects.filter(follower=target_user).count()
        
        data = {
            'followers_count': followers_count,
            'following_count': following_count,
        }
        
        # Check if current user is following target user (if different users)
        if target_user != request.user:
            is_following = Follow.objects.filter(
                follower=request.user,
                following=target_user
            ).exists()
            data['is_following'] = is_following
        
        serializer = FollowStatsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
