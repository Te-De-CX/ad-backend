from rest_framework import serializers
from .models import Task, UserTask

class TaskSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'video', 'video_url',
            'bronze_price', 'silver_price', 'gold_price',
            'bronze_reward', 'silver_reward', 'gold_reward',
            'requires_subscription', 'is_active', 'created_at',
        ]

    def get_video_url(self, obj):
        request = self.context.get('request')
        if obj.video and request:
            return request.build_absolute_uri(obj.video.url)
        return None


class UserTaskSerializer(serializers.ModelSerializer):
    task_title = serializers.ReadOnlyField(source='task.title')
    task_description = serializers.ReadOnlyField(source='task.description')
    task_video_url = serializers.SerializerMethodField()
    bronze_price = serializers.ReadOnlyField(source='task.bronze_price')
    silver_price = serializers.ReadOnlyField(source='task.silver_price')
    gold_price = serializers.ReadOnlyField(source='task.gold_price')
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = UserTask
        fields = [
            'id', 'user', 'task', 'tier', 'status',
            'task_title', 'task_description', 'task_video_url',
            'bronze_price', 'silver_price', 'gold_price',
            'reward_amount', 'payment_proof', 'completion_proof',
            'admin_notes', 'started_at', 'completed_at', 'user_email',
        ]
        read_only_fields = ['user', 'started_at', 'reward_amount']

    def get_task_video_url(self, obj):
        request = self.context.get('request')
        if obj.task.video and request:
            return request.build_absolute_uri(obj.task.video.url)
        return None