# tasks/serializers.py
from rest_framework import serializers
from .models import Task, UserTask

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class UserTaskSerializer(serializers.ModelSerializer):
    task_title = serializers.ReadOnlyField(source='task.title')
    task_description = serializers.ReadOnlyField(source='task.description')
    task_reward = serializers.ReadOnlyField(source='task.reward_amount')
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = UserTask
        fields = '__all__'
        read_only_fields = ['user', 'started_at']