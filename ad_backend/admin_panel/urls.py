# admin_panel/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminDashboardView, AdminUserManagementViewSet, AdminInvestmentViewSet,
    AdminTaskViewSet, AdminTransactionViewSet, SystemSettingsViewSet,
    AdminChallengeViewSet  # Add this import
)

router = DefaultRouter()
router.register('users', AdminUserManagementViewSet, basename='admin-user')
router.register('investments', AdminInvestmentViewSet, basename='admin-investment')
router.register('tasks', AdminTaskViewSet, basename='admin-task')
router.register('transactions', AdminTransactionViewSet, basename='admin-transaction')
router.register('settings', SystemSettingsViewSet, basename='admin-setting')
router.register('challenges', AdminChallengeViewSet, basename='admin-challenge')  # Add this line

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('', include(router.urls)),
]