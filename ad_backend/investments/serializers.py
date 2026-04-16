# investments/serializers.py
from rest_framework import serializers
from .models import InvestmentPlan, Investment, Transaction, InvestmentAccess

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
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['id', 'user', 'reference', 'created_at']

class InvestmentAccessSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    user_username = serializers.ReadOnlyField(source='user.username')
    plan_name = serializers.ReadOnlyField(source='investment.plan.name')
    investment_amount = serializers.ReadOnlyField(source='investment.amount')
    
    class Meta:
        model = InvestmentAccess
        fields = [
            'id', 'user', 'user_email', 'user_username', 'investment',
            'plan_name', 'investment_amount', 'is_approved', 'approved_by',
            'approved_at', 'payment_proof', 'payment_reference', 'admin_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved_at']