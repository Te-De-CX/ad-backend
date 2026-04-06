# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, UserProfileView,
    UpdateAccountInfoView, MyActivitiesView, CheckSubscriptionView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('update-account/', UpdateAccountInfoView.as_view(), name='update_account'),
    path('my-activities/', MyActivitiesView.as_view(), name='my_activities'),
    path('check-subscription/', CheckSubscriptionView.as_view(), name='check_subscription'),
]