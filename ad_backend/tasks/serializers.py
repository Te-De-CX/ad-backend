# tasks/serializers.py
from rest_framework import serializers
from .models import Task, UserTask

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class UserTaskSerializer(serializers.ModelSerializer):
    task_title = serializers.ReadOnlyField()
    task_description = serializers.ReadOnlyField()
    task_video_url = serializers.ReadOnlyField()
    reward_amount = serializers.ReadOnlyField()
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = UserTask
        fields = [
            'id', 'user', 'task', 'tier', 'status', 'payment_proof', 'completion_proof',
            'admin_notes', 'started_at', 'completed_at', 'task_title', 'task_description',
            'task_video_url', 'reward_amount', 'user_email'
        ]
        read_only_fields = ['id', 'user', 'started_at', 'completed_at']