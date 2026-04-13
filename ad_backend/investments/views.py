from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.utils import timezone
from decimal import Decimal
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
        if getattr(self, 'swagger_fake_view', False):
            return Investment.objects.none()
        return Investment.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        investment = serializer.save(user=self.request.user, status='pending')

        Transaction.objects.create(
            user=self.request.user,
            transaction_type='deposit',
            amount=investment.amount,
            net_amount=investment.amount,
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

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        return Transaction.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class WithdrawalRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        method = request.data.get('method')
        wallet_details = request.data.get('wallet_details')

        # Validate
        if not amount:
            return Response({'error': 'Amount is required'}, status=400)

        try:
            amount = Decimal(str(amount))
        except Exception:
            return Response({'error': 'Invalid amount'}, status=400)

        if amount < 500:
            return Response({'error': 'Minimum withdrawal is $500'}, status=400)

        if not method:
            return Response({'error': 'Withdrawal method is required'}, status=400)

        if not wallet_details:
            return Response({'error': 'Payment details are required'}, status=400)

        fee = amount * Decimal('0.05')
        net_amount = amount - fee

        transaction = Transaction.objects.create(
            user=request.user,
            transaction_type='withdrawal',
            amount=amount,
            fee=fee,
            net_amount=net_amount,
            status='pending',
            reference=f"WD_{uuid.uuid4().hex[:10].upper()}",
            withdrawal_method=method,
            withdrawal_details=wallet_details,
            description=f"Withdrawal via {method} | Net: ${net_amount:.2f} after 5% fee"
        )

        ActivityLog.objects.create(
            user=request.user,
            action=f"Withdrawal request of ${amount} via {method}",
            ip_address=self.get_client_ip(request)
        )

        return Response({
            'message': 'Withdrawal request submitted successfully',
            'reference': transaction.reference,
            'amount': str(amount),
            'fee': str(fee),
            'net_amount': str(net_amount),
            'status': 'pending',
        }, status=201)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')