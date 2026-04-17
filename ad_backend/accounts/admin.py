# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import User, UserProfile, ActivityLog

# accounts/admin.py - Update CustomUserAdmin
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'plain_password', 'role', 'is_subscribed', 'is_active', 'created_at')
    list_filter = ('role', 'is_subscribed', 'is_active', 'created_at')
    search_fields = ('email', 'username', 'plain_password', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password', 'plain_password')}),
        ('Personal Info', {'fields': ('phone_number', 'address')}),
        ('Account Information', {'fields': ('bank_name', 'account_number', 'account_name', 
                                           'btc_wallet', 'eth_wallet', 'usdt_wallet')}),
        ('Subscription', {'fields': ('is_subscribed', 'subscription_start_date', 'subscription_end_date')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 
                                   'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )

class UserProfileAdmin(admin.ModelAdmin):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    
    MARITAL_STATUS_CHOICES = (
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    )
    
    HEARING_STATUS_CHOICES = (
        ('good', 'Good'),
        ('partial', 'Partial Hearing Loss'),
        ('full', 'Full Hearing Loss'),
        ('impaired', 'Hearing Impaired'),
    )
    
    HOUSING_CHOICES = (
        ('own', 'Own House'),
        ('rent', 'Rented'),
        ('lease', 'Leasing'),
        ('family', 'Living with Family'),
        ('other', 'Other'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('bank', 'Bank Transfer'),
        ('btc', 'Bitcoin'),
        ('eth', 'Ethereum'),
        ('usdt', 'USDT'),
        ('cash', 'Cash'),
    )
    
    list_display = ('user', 'full_name', 'challenge_status', 'registration_fee_paid', 
                   'insurance_fee_paid', 'challenge_start_date')
    list_filter = ('challenge_status', 'registration_fee_paid', 'insurance_fee_paid', 
                  'gender', 'marital_status')
    search_fields = ('user__email', 'full_name', 'contact_number')
    readonly_fields = ('participant_signature_date', 'ceo_signature_date', 
                      'challenge_completed_date', 'user_created_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'profile_picture')
        }),
        ('Personal Details', {
            'fields': ('gender', 'age', 'date_of_birth', 'marital_status', 
                      'contact_number', 'address', 'location')
        }),
        ('Financial Information', {
            'fields': ('monthly_income', 'preferred_payment_method')
        }),
        ('Challenge Information', {
            'fields': ('challenge_status', 'challenge_start_date', 'challenge_end_date',
                      'total_prize', 'registration_fee_paid', 'insurance_fee_paid',
                      'registration_fee_amount', 'insurance_fee_amount')
        }),
        ('Medical Information', {
            'fields': ('hearing_status', 'housing_situation')
        }),
        ('Signatures', {
            'fields': ('participant_signature', 'participant_signature_date',
                      'ceo_signature', 'ceo_signature_date')
        }),
        ('Completion & Admin', {
            'fields': ('challenge_completed_date', 'challenge_reward_claimed', 'admin_notes')
        }),
    )
    
    def user_created_at(self, obj):
        return obj.user.created_at
    user_created_at.short_description = 'User Created At'
    
    actions = ['approve_registration_fee', 'approve_insurance_fee', 'start_challenge', 'complete_challenge']
    
    def approve_registration_fee(self, request, queryset):
        updated = queryset.update(registration_fee_paid=True)
        self.message_user(request, f'{updated} registration fees approved.')
    approve_registration_fee.short_description = "Approve registration fees"
    
    def approve_insurance_fee(self, request, queryset):
        updated = queryset.update(insurance_fee_paid=True)
        self.message_user(request, f'{updated} insurance fees approved.')
    approve_insurance_fee.short_description = "Approve insurance fees"
    
    def start_challenge(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(challenge_status='active', challenge_start_date=timezone.now())
        self.message_user(request, f'{updated} challenges started.')
    start_challenge.short_description = "Start selected challenges"
    
    def complete_challenge(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(challenge_status='completed', challenge_completed_date=timezone.now())
        self.message_user(request, f'{updated} challenges completed.')
    complete_challenge.short_description = "Complete selected challenges"

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'action', 'details')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)