# investments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvestmentPlanViewSet, InvestmentViewSet, TransactionViewSet,
    InvestmentAccessViewSet
)

router = DefaultRouter()
router.register('plans', InvestmentPlanViewSet, basename='investment-plan')
router.register('investments', InvestmentViewSet, basename='investment')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('access-requests', InvestmentAccessViewSet, basename='investment-access')

urlpatterns = [
    path('', include(router.urls)),
]