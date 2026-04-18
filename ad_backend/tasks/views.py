# tasks/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Task, UserTask
from .serializers import TaskSerializer, UserTaskSerializer
from accounts.models import ActivityLog

class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get tasks available for the user"""
        # Get tasks the user hasn't started or completed
        user_task_ids = UserTask.objects.filter(user=request.user).values_list('task_id', flat=True)
        queryset = Task.objects.filter(is_active=True).exclude(id__in=user_task_ids)
        
        # Filter by subscription
        if not request.user.has_subscription():
            queryset = queryset.filter(requires_subscription=False)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start_task(self, request, pk=None):
        """Start a task with selected tier"""
        task = self.get_object()
        tier = request.data.get('tier', 'bronze')
        
        # Check if user already has this task
        if UserTask.objects.filter(user=request.user, task=task).exists():
            return Response(
                {'error': 'You have already started this task'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check subscription requirement
        if task.requires_subscription and not request.user.has_subscription():
            return Response(
                {'error': 'This task requires a premium subscription'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create user task
        user_task = UserTask.objects.create(
            user=request.user,
            task=task,
            tier=tier,
            status='pending_payment'
        )
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Started task: {task.title} ({tier} tier)",
            ip_address=self.get_client_ip(request)
        )
        
        serializer = UserTaskSerializer(user_task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserTaskViewSet(viewsets.ModelViewSet):
    serializer_class = UserTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserTask.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get all tasks for the current user"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_payment(self, request, pk=None):
        """Upload payment proof"""
        user_task = self.get_object()
        
        if user_task.status != 'pending_payment':
            return Response(
                {'error': f'Cannot upload payment for task with status: {user_task.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_proof = request.FILES.get('payment_proof')
        if not payment_proof:
            return Response(
                {'error': 'Payment proof file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_task.payment_proof = payment_proof
        user_task.status = 'pending_review'
        user_task.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Uploaded payment proof for task: {user_task.task.title}",
            ip_address=self.get_client_ip(request)
        )
        
        return Response({'status': 'success', 'message': 'Payment proof uploaded successfully'})
    
    @action(detail=True, methods=['post'])
    def upload_completion(self, request, pk=None):
        """Upload completion proof"""
        user_task = self.get_object()
        
        if user_task.status != 'in_progress':
            return Response(
                {'error': f'Cannot upload completion for task with status: {user_task.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        completion_proof = request.FILES.get('completion_proof')
        if not completion_proof:
            return Response(
                {'error': 'Completion proof file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_task.completion_proof = completion_proof
        user_task.status = 'pending_review'
        user_task.completed_at = timezone.now()
        user_task.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Submitted completion for task: {user_task.task.title}",
            ip_address=self.get_client_ip(request)
        )
        
        return Response({'status': 'success', 'message': 'Completion proof submitted successfully'})
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip