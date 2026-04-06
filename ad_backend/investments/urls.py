# investments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestmentPlanViewSet, InvestmentViewSet, TransactionViewSet

router = DefaultRouter()
router.register('plans', InvestmentPlanViewSet, basename='investment-plan')
router.register('investments', InvestmentViewSet, basename='investment')
router.register('transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]