# investments/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import InvestmentPlan, Investment, Transaction
from .serializers import InvestmentPlanSerializer, InvestmentSerializer, TransactionSerializer
from accounts.models import ActivityLog
import uuid

class InvestmentPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InvestmentPlan.objects.filter(is_active=True)
    serializer_class = InvestmentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Check if this is for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Investment.objects.none()
        return Investment.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        investment = serializer.save(user=self.request.user, status='pending')
        
        # Create transaction record
        Transaction.objects.create(
            user=self.request.user,
            transaction_type='deposit',
            amount=investment.amount,
            status='pending',
            reference=f"INV_{investment.id}_{uuid.uuid4().hex[:10]}",
            description=f"Investment in {investment.plan.name}"
        )
        
        ActivityLog.objects.create(
            user=self.request.user,
            action=f"Created investment of ${investment.amount} in {investment.plan.name}",
            ip_address=self.get_client_ip()
        )
    
    @action(detail=False, methods=['get'])
    def my_investments(self, request):
        investments = self.get_queryset()
        serializer = self.get_serializer(investments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        investment = self.get_object()
        
        if investment.status != 'completed':
            return Response({'error': 'Investment not completed yet'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create withdrawal request
        transaction = Transaction.objects.create(
            user=request.user,
            transaction_type='withdrawal',
            amount=investment.total_profit + investment.amount,
            status='pending',
            reference=f"WTH_{investment.id}_{uuid.uuid4().hex[:10]}",
            description=f"Withdrawal from investment #{investment.id}"
        )
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Requested withdrawal of ${transaction.amount} from investment #{investment.id}",
            ip_address=self.get_client_ip()
        )
        
        return Response({'status': 'withdrawal_requested', 'transaction_id': transaction.id})
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Check if this is for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')