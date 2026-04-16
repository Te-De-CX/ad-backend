# admin_panel/serializers.py
from rest_framework import serializers
from accounts.models import User
from investments.models import Investment, Transaction
from tasks.models import Task
from .models import AdminAction, SystemSettings
from accounts.models import UserProfile, User

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone_number']

class ChallengeParticipantSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'full_name', 'gender', 'age', 'monthly_income',
            'marital_status', 'contact_number', 'hearing_status', 'housing_situation',
            'preferred_payment_method', 'location', 'challenge_status',
            'registration_fee_paid', 'insurance_fee_paid', 'total_prize',
            'challenge_start_date', 'challenge_end_date', 'participant_signature',
            'participant_signature_date', 'ceo_signature', 'ceo_signature_date',
            'challenge_completed_date', 'challenge_reward_claimed', 'admin_notes'
        ]

class UserManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'is_subscribed', 
                  'phone_number', 'created_at', 'subscription_end_date']

class InvestmentManagementSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    plan_name = serializers.ReadOnlyField(source='plan.name')
    
    class Meta:
        model = Investment
        fields = '__all__'

class TaskManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Transaction
        fields = '__all__'
        ref_name = 'AdminTransaction'  # Add unique ref_name

class AdminActionSerializer(serializers.ModelSerializer):
    admin_email = serializers.ReadOnlyField(source='admin.email')
    target_user_email = serializers.ReadOnlyField(source='target_user.email')
    
    class Meta:
        model = AdminAction
        fields = '__all__'

class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = '__all__'

class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    total_investments = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_tasks_completed = serializers.IntegerField()
    pending_transactions = serializers.IntegerField()