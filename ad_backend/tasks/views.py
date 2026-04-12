from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Task, UserTask
from .serializers import TaskSerializer, UserTaskSerializer
from accounts.models import ActivityLog


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.filter(is_active=True)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['post'])
    def start_task(self, request, pk=None):
        task = self.get_object()
        tier = request.data.get('tier')

        if tier not in ['bronze', 'silver', 'gold']:
            return Response({'error': 'Invalid tier'}, status=400)

        # Prevent duplicate active attempts
        active = UserTask.objects.filter(
            user=request.user,
            task=task,
            status__in=['pending_payment', 'pending_review', 'in_progress']
        ).exists()

        if active:
            return Response(
                {'error': 'You already have an active attempt for this task'},
                status=400
            )

        # reward_amount auto-set by model save()
        user_task = UserTask.objects.create(
            user=request.user,
            task=task,
            tier=tier,
            status='pending_payment'
        )

        ActivityLog.objects.create(
            user=request.user,
            action=f"Started task: {task.title} ({tier})"
        )

        return Response(
            UserTaskSerializer(user_task, context={'request': request}).data,
            status=201
        )

    @action(detail=True, methods=['post'])
    def upload_payment(self, request, pk=None):
        task = self.get_object()

        user_task = UserTask.objects.filter(
            user=request.user,
            task=task,
            status='pending_payment'
        ).last()

        if not user_task:
            return Response({'error': 'No pending payment found'}, status=400)

        file = request.FILES.get('payment_proof')

        if not file:
            return Response({'error': 'Payment proof is required'}, status=400)

        if file.size > 5 * 1024 * 1024:
            return Response({'error': 'File too large (max 5MB)'}, status=400)

        user_task.payment_proof = file
        user_task.status = 'pending_review'
        user_task.save()

        ActivityLog.objects.create(
            user=request.user,
            action=f"Uploaded payment proof for: {task.title}"
        )

        return Response({'message': 'Payment submitted for review'})

    @action(detail=True, methods=['post'])
    def complete_task(self, request, pk=None):
        task = self.get_object()

        user_task = UserTask.objects.filter(
            user=request.user,
            task=task,
            status='in_progress'
        ).last()

        if not user_task:
            return Response({'error': 'No active task in progress'}, status=400)

        file = request.FILES.get('completion_proof')

        if not file:
            return Response({'error': 'Completion proof is required'}, status=400)

        if file.size > 5 * 1024 * 1024:
            return Response({'error': 'File too large (max 5MB)'}, status=400)

        user_task.completion_proof = file
        user_task.status = 'pending_review'
        user_task.save()

        ActivityLog.objects.create(
            user=request.user,
            action=f"Submitted completion proof for: {task.title}"
        )

        return Response({'message': 'Task submitted for approval'})


class MyTasksView(generics.ListAPIView):
    serializer_class = UserTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserTask.objects.filter(
            user=self.request.user
        ).order_by('-started_at')

    def get_serializer_context(self):
        return {'request': self.request}


class AvailableTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        completed_tasks = UserTask.objects.filter(
            user=self.request.user,
            status='completed'
        ).values_list('task_id', flat=True)

        tasks = Task.objects.filter(is_active=True)

        if not self.request.user.has_subscription():
            tasks = tasks.filter(requires_subscription=False)

        return tasks.exclude(id__in=completed_tasks)

    def get_serializer_context(self):
        return {'request': self.request}