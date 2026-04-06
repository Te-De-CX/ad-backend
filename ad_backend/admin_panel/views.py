# admin_panel/views.py (add these lines at the beginning of each ViewSet)
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count, Q
from django.utils import timezone
from accounts.models import User, ActivityLog
from investments.models import Investment, Transaction
from tasks.models import Task, UserTask
from .models import AdminAction, SystemSettings
from .serializers import (
    UserManagementSerializer, InvestmentManagementSerializer, 
    TaskManagementSerializer, TransactionSerializer, AdminActionSerializer,
    SystemSettingsSerializer, DashboardStatsSerializer
)
from .permissions import IsAdminUser

# In admin_panel/views.py, update the AdminDashboardView:

class AdminDashboardView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = DashboardStatsSerializer  # Add this line
    
    def get(self, request):
        total_users = User.objects.count()
        active_subscriptions = User.objects.filter(is_subscribed=True).count()
        total_investments = Investment.objects.filter(status='active').aggregate(total=Sum('amount'))['total'] or 0
        total_tasks_completed = UserTask.objects.filter(status='completed').count()
        pending_transactions = Transaction.objects.filter(status='pending').count()
        
        recent_users = User.objects.order_by('-created_at')[:10]
        recent_activities = ActivityLog.objects.order_by('-created_at')[:20]
        
        stats = {
            'total_users': total_users,
            'active_subscriptions': active_subscriptions,
            'total_investments': total_investments,
            'total_tasks_completed': total_tasks_completed,
            'pending_transactions': pending_transactions,
            'recent_users': UserManagementSerializer(recent_users, many=True).data,
            'recent_activities': list(recent_activities.values('user__email', 'action', 'created_at'))
        }
        
        serializer = self.get_serializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class AdminUserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def toggle_subscription(self, request, pk=None):
        user = self.get_object()
        user.is_subscribed = not user.is_subscribed
        if user.is_subscribed:
            user.subscription_start_date = timezone.now()
            user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
        user.save()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Toggle Subscription",
            target_user=user,
            details=f"Subscription status changed to {user.is_subscribed}"
        )
        
        return Response({'status': 'updated', 'is_subscribed': user.is_subscribed})
    
    @action(detail=True, methods=['post'])
    def update_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get('role')
        if new_role in ['user', 'admin', 'super_admin']:
            user.role = new_role
            user.save()
            
            AdminAction.objects.create(
                admin=request.user,
                action_type="Update Role",
                target_user=user,
                details=f"Role updated to {new_role}"
            )
            
            return Response({'status': 'updated', 'role': user.role})
        return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def delete_user(self, request, pk=None):
        user = self.get_object()
        user_email = user.email
        user.delete()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Delete User",
            details=f"Deleted user: {user_email}"
        )
        
        return Response({'status': 'deleted'})

class AdminInvestmentViewSet(viewsets.ModelViewSet):
    queryset = Investment.objects.all()
    serializer_class = InvestmentManagementSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def approve_investment(self, request, pk=None):
        investment = self.get_object()
        investment.status = 'active'
        investment.start_date = timezone.now()
        investment.end_date = timezone.now() + timezone.timedelta(days=investment.plan.duration_days)
        investment.save()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Approve Investment",
            target_user=investment.user,
            details=f"Approved investment of ${investment.amount} in {investment.plan.name}"
        )
        
        return Response({'status': 'approved'})

class AdminTaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskManagementSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def create_task(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Create Task",
            details=f"Created task: {task.title}"
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def assign_task_to_user(self, request, pk=None):
        task = self.get_object()
        user_id = request.data.get('user_id')
        user = User.objects.get(id=user_id)
        
        user_task, created = UserTask.objects.get_or_create(user=user, task=task)
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Assign Task",
            target_user=user,
            details=f"Assigned task: {task.title}"
        )
        
        return Response({'status': 'assigned', 'created': created})

class AdminTransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def approve_transaction(self, request, pk=None):
        transaction = self.get_object()
        transaction.status = 'completed'
        transaction.admin_notes = request.data.get('notes', '')
        transaction.save()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Approve Transaction",
            target_user=transaction.user,
            details=f"Approved {transaction.transaction_type} of ${transaction.amount}"
        )
        
        return Response({'status': 'approved'})

class SystemSettingsViewSet(viewsets.ModelViewSet):
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def get_by_key(self, request):
        key = request.query_params.get('key')
        try:
            setting = SystemSettings.objects.get(key=key)
            return Response({'key': setting.key, 'value': setting.value})
        except SystemSettings.DoesNotExist:
            return Response({'error': 'Setting not found'}, status=status.HTTP_404_NOT_FOUND)