# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, ActivityLog

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'role', 'is_subscribed', 'is_active', 'created_at')
    list_filter = ('role', 'is_subscribed', 'is_active', 'created_at')
    search_fields = ('email', 'username', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
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
    list_display = ('user', 'country', 'city', 'referral_code', 'get_user_created_at')
    list_filter = ('country',)
    search_fields = ('user__email', 'user__username', 'referral_code')
    readonly_fields = ('get_user_created_at',)
    
    def get_user_created_at(self, obj):
        return obj.user.created_at
    get_user_created_at.short_description = 'User Created At'
    get_user_created_at.admin_order_field = 'user__created_at'

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