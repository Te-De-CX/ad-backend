# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, ActivityLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'phone_number', 'address', 
                  'is_subscribed', 'subscription_start_date', 'subscription_end_date',
                  'bank_name', 'account_number', 'account_name', 'btc_wallet', 
                  'eth_wallet', 'usdt_wallet', 'created_at']
        read_only_fields = ['id', 'role', 'is_subscribed', 'created_at']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'confirm_password', 'phone_number']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        if 'phone_number' in validated_data:
            user.phone_number = validated_data['phone_number']
            user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        return {'user': user}

class UpdateAccountInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['bank_name', 'account_number', 'account_name', 'btc_wallet', 
                  'eth_wallet', 'usdt_wallet', 'phone_number', 'address']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user']

class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = ActivityLog
        fields = '__all__'
        read_only_fields = ['user', 'created_at']