from django.urls import path
from .views.views import (
    AuthorRegistrationView,
    InstitutionRegistrationView,
    LoginView,
    LogoutView,
    CookieTokenRefreshView,
    MeView,
    AuthorProfileView,
    InstitutionProfileView,
    ChangePasswordView,
    UpdateEmailView,
    AccountStatusView,
    DeactivateAccountView,
    DeleteAccountView,
    RefreshAuthorStatsView
)
from .views.follow.views import (
    FollowUserView,
    UnfollowUserView,
    MyFollowersView,
    MyFollowingView,
    UserFollowersView,
    UserFollowingView,
    FollowStatsView,
)

urlpatterns = [
    # Registration endpoints
    path('register/author/', AuthorRegistrationView.as_view(), name='author-register'),
    path('register/institution/', InstitutionRegistrationView.as_view(), name='institution-register'),
    
    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
    
    # Current user profile (me)
    path('me/', MeView.as_view(), name='me'),
    
    # Profile endpoints
    path('profile/author/', AuthorProfileView.as_view(), name='author-profile'),
    path('profile/institution/', InstitutionProfileView.as_view(), name='institution-profile'),
    path('profile/author/refresh-stats/', RefreshAuthorStatsView.as_view(), name='refresh-author-stats'),
    
    # Account Settings endpoints
    path('settings/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('settings/update-email/', UpdateEmailView.as_view(), name='update-email'),
    path('settings/account-status/', AccountStatusView.as_view(), name='account-status'),
    path('settings/deactivate-account/', DeactivateAccountView.as_view(), name='deactivate-account'),
    path('settings/delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    
    # Follow endpoints
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/<int:user_id>/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('followers/', MyFollowersView.as_view(), name='my-followers'),
    path('following/', MyFollowingView.as_view(), name='my-following'),
    path('users/<int:user_id>/followers/', UserFollowersView.as_view(), name='user-followers'),
    path('users/<int:user_id>/following/', UserFollowingView.as_view(), name='user-following'),
    path('follow-stats/', FollowStatsView.as_view(), name='my-follow-stats'),
    path('users/<int:user_id>/follow-stats/', FollowStatsView.as_view(), name='user-follow-stats'),
]