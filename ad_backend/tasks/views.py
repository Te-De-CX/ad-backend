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
        tier = request.data.get('tier')

        if tier not in ['bronze', 'silver', 'gold']:
            return Response({'error': 'Invalid tier'}, status=400)

        # 💰 Determine reward
        reward_map = {
            'bronze': task.bronze_reward,
            'silver': task.silver_reward,
            'gold': task.gold_reward,
        }

        user_task, created = UserTask.objects.get_or_create(
            user=request.user,
            task=task,
            defaults={
                'tier': tier,
                'reward_amount': reward_map[tier],
                'status': 'pending_payment'
            }
        )

        if not created:
            return Response({'error': 'Task already started'}, status=400)

        return Response({
            'message': 'Proceed to payment via WhatsApp',
            'tier': tier
        })

    @action(detail=True, methods=['post'])
    def upload_payment(self, request, pk=None):
        task = self.get_object()
        user_task = get_object_or_404(UserTask, user=request.user, task=task)

        user_task.payment_proof = request.FILES.get('payment_proof')
        user_task.status = 'pending'
        user_task.save()

        return Response({'message': 'Payment submitted for review'})

    @action(detail=True, methods=['post'])
    def complete_task(self, request, pk=None):
        task = self.get_object()
        user_task = get_object_or_404(UserTask, user=request.user, task=task)

        user_task.completion_proof = request.FILES.get('completion_proof')
        user_task.status = 'pending'
        user_task.save()

        return Response({'message': 'Task submitted for approval'})


class MyTasksView(generics.ListAPIView):
    serializer_class = UserTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserTask.objects.filter(user=self.request.user).order_by('-started_at')


class AvailableTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        completed_tasks = UserTask.objects.filter(
            user=self.request.user,
            status='completed'
        ).values_list('task_id', flat=True)

        tasks = Task.objects.filter(is_active=True).exclude(id__in=completed_tasks)

        if not self.request.user.has_subscription():
            tasks = tasks.filter(requires_subscription=False)

        return tasks