# tasks/views.py
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Task, UserTask
from .serializers import TaskSerializer, UserTaskSerializer
from accounts.models import ActivityLog

class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.filter(is_active=True)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def start_task(self, request, pk=None):
        task = self.get_object()
        
        # Check subscription requirement
        if task.requires_subscription and not request.user.has_subscription():
            return Response({'error': 'This task requires an active subscription'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        user_task, created = UserTask.objects.get_or_create(
            user=request.user,
            task=task,
            defaults={'status': 'in_progress'}
        )
        
        if not created and user_task.status == 'completed':
            return Response({'error': 'Task already completed'}, status=status.HTTP_400_BAD_REQUEST)
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Started task: {task.title}",
            ip_address=self.get_client_ip(request)
        )
        
        return Response(UserTaskSerializer(user_task).data)
    
    @action(detail=True, methods=['post'])
    def complete_task(self, request, pk=None):
        task = self.get_object()
        user_task = get_object_or_404(UserTask, user=request.user, task=task)
        
        if user_task.status == 'completed':
            return Response({'error': 'Task already completed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Here you would process payment through admin
        # Since no payment integration, we mark as pending admin approval
        user_task.status = 'pending'
        user_task.completion_proof = request.FILES.get('completion_proof')
        user_task.save()
        
        # Create transaction record for reward
        from investments.models import Transaction
        import uuid
        Transaction.objects.create(
            user=request.user,
            transaction_type='bonus',
            amount=task.reward_amount,
            status='pending',
            reference=f"TASK_{task.id}_{uuid.uuid4().hex[:10]}",
            description=f"Reward for completing task: {task.title}"
        )
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Completed task: {task.title}",
            ip_address=self.get_client_ip(request)
        )
        
        return Response({'status': 'pending_approval', 'message': 'Task submitted for admin approval'})
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class MyTasksView(generics.ListAPIView):
    serializer_class = UserTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserTask.objects.filter(user=self.request.user).order_by('-started_at')

class AvailableTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Get tasks not completed by user
        completed_tasks = UserTask.objects.filter(
            user=self.request.user, 
            status='completed'
        ).values_list('task_id', flat=True)
        
        tasks = Task.objects.filter(is_active=True).exclude(id__in=completed_tasks)
        
        # Filter by subscription if user doesn't have subscription
        if not self.request.user.has_subscription():
            tasks = tasks.filter(requires_subscription=False)
        
        return tasks