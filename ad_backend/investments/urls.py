from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvestmentPlanViewSet,
    InvestmentViewSet,
    TransactionViewSet,
    WithdrawalRequestView,
)

router = DefaultRouter()
router.register('plans', InvestmentPlanViewSet, basename='investment-plan')
router.register('investments', InvestmentViewSet, basename='investment')
router.register('transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('withdrawal-request/', WithdrawalRequestView.as_view(), name='withdrawal-request'),
]