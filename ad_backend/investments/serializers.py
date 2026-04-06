# investments/serializers.py
from rest_framework import serializers
from .models import InvestmentPlan, Investment, Transaction

class InvestmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentPlan
        fields = '__all__'

class InvestmentSerializer(serializers.ModelSerializer):
    plan_name = serializers.ReadOnlyField(source='plan.name')
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Investment
        fields = ['id', 'user', 'plan', 'plan_name', 'user_email', 'amount', 
                  'daily_profit', 'total_profit', 'status', 'start_date', 
                  'end_date', 'created_at']
        read_only_fields = ['id', 'user', 'daily_profit', 'total_profit', 
                           'status', 'start_date', 'end_date', 'created_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['id', 'user', 'reference', 'created_at']
        ref_name = 'InvestmentTransaction'  # Add unique ref_name