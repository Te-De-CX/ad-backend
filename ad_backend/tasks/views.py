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

    # Uses UserTask.id — detail=False with url_path capturing user_task_id
    @action(detail=False, methods=['post'], url_path='upload-payment/(?P<user_task_id>[0-9]+)')
    def upload_payment(self, request, user_task_id=None):
        try:
            user_task = UserTask.objects.get(
                id=user_task_id,
                user=request.user,
                status='pending_payment'
            )
        except UserTask.DoesNotExist:
            return Response(
                {'error': 'No pending payment found for this task'},
                status=400
            )

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
            action=f"Uploaded payment proof for: {user_task.task.title}"
        )

        return Response(
            UserTaskSerializer(user_task, context={'request': request}).data
        )

    # Uses UserTask.id — detail=False with url_path capturing user_task_id
    @action(detail=False, methods=['post'], url_path='complete-task/(?P<user_task_id>[0-9]+)')
    def complete_task(self, request, user_task_id=None):
        try:
            user_task = UserTask.objects.get(
                id=user_task_id,
                user=request.user,
                status='in_progress'
            )
        except UserTask.DoesNotExist:
            return Response(
                {'error': 'No in-progress task found with this ID'},
                status=400
            )

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
            action=f"Submitted completion proof for: {user_task.task.title}"
        )

        return Response(
            UserTaskSerializer(user_task, context={'request': request}).data
        )


class MyTasksView(generics.ListAPIView):
    serializer_class = UserTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserTask.objects.filter(
            user=self.request.user
        ).select_related('task').order_by('-started_at')

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