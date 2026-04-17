# investments/views.py
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import InvestmentPlan, Investment, Transaction, InvestmentAccess
from .serializers import (
    InvestmentPlanSerializer, InvestmentSerializer, 
    TransactionSerializer, InvestmentAccessSerializer
)
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
        if getattr(self, 'swagger_fake_view', False):
            return Investment.objects.none()
        return Investment.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        investment = serializer.save(user=self.request.user, status='pending')
        
        # Create access request
        InvestmentAccess.objects.create(
            user=self.request.user,
            investment=investment,
            payment_reference=f"INV_{investment.id}_{uuid.uuid4().hex[:8]}"
        )
        
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
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')

class InvestmentAccessViewSet(viewsets.ModelViewSet):
    """ViewSet for managing investment access requests"""
    serializer_class = InvestmentAccessSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return InvestmentAccess.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def approve_access(self, request, pk=None):
        access_request = self.get_object()
        
        if access_request.is_approved:
            return Response({'error': 'Access already approved'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Approve the access request
        access_request.is_approved = True
        access_request.approved_by = request.user
        access_request.approved_at = timezone.now()
        access_request.save()
        
        # Also activate the associated investment
        investment = access_request.investment
        investment.status = 'active'
        investment.start_date = timezone.now()
        investment.end_date = timezone.now() + timezone.timedelta(days=investment.plan.duration_days)
        investment.save()
        
        # Update the related transaction
        transaction = Transaction.objects.filter(
            user=access_request.user,
            reference__contains=f"INV_{investment.id}"
        ).first()
        
        if transaction:
            transaction.status = 'completed'
            transaction.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Approved investment access for {access_request.user.email}",
            details=f"Approved investment of ${investment.amount} in {investment.plan.name}",
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'status': 'approved',
            'message': 'Investment access approved successfully'
        })
    
    @action(detail=True, methods=['post'])
    def reject_access(self, request, pk=None):
        access_request = self.get_object()
        
        if access_request.is_approved:
            return Response({'error': 'Cannot reject already approved access'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as rejected by deleting or setting a rejected flag
        admin_notes = request.data.get('admin_notes', 'Rejected by admin')
        access_request.admin_notes = admin_notes
        access_request.save()
        
        # Optionally delete or mark the investment as cancelled
        investment = access_request.investment
        investment.status = 'cancelled'
        investment.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Rejected investment access for {access_request.user.email}",
            details=f"Rejected investment of ${investment.amount} in {investment.plan.name}. Reason: {admin_notes}",
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'status': 'rejected',
            'message': 'Investment access rejected'
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip