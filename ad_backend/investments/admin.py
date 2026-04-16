# investments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import InvestmentPlan, Investment, Transaction, InvestmentAccess

class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_amount', 'max_amount', 'daily_interest_rate', 
                   'duration_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'daily_interest_rate', 'duration_days')
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'description')
        }),
        ('Financial Settings', {
            'fields': ('min_amount', 'max_amount', 'daily_interest_rate', 'duration_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'amount', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'plan', 'created_at')
    search_fields = ('user__email', 'user__username', 'plan__name')
    readonly_fields = ('created_at', 'updated_at', 'daily_profit', 'total_profit')
    actions = ['approve_investments', 'complete_investments']
    
    def approve_investments(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        self.message_user(request, f'{updated} investments approved.')
    approve_investments.short_description = "Approve selected investments"
    
    def complete_investments(self, request, queryset):
        updated = queryset.filter(status='active').update(
            status='completed',
            end_date=timezone.now()
        )
        self.message_user(request, f'{updated} investments completed.')
    complete_investments.short_description = "Complete selected investments"
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Investment Details', {
            'fields': ('plan', 'amount', 'status')
        }),
        ('Profit Information', {
            'fields': ('daily_profit', 'total_profit')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at')
        }),
    )

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'transaction_type', 'amount', 'status', 'reference', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('user__email', 'reference', 'description')
    readonly_fields = ('created_at', 'updated_at', 'reference')
    actions = ['approve_transactions', 'reject_transactions']
    
    def approve_transactions(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='completed')
        self.message_user(request, f'{updated} transactions approved.')
    approve_transactions.short_description = "Approve selected transactions"
    
    def reject_transactions(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f'{updated} transactions rejected.')
    reject_transactions.short_description = "Reject selected transactions"
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('user', 'transaction_type', 'amount', 'status', 'reference')
        }),
        ('Description', {
            'fields': ('description', 'admin_notes')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

class InvestmentAccessAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'investment', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__email', 'payment_reference')
    readonly_fields = ('created_at', 'updated_at', 'approved_at')
    actions = ['approve_access_requests']
    
    def approve_access_requests(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_approved=False).update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} access requests approved.')
    approve_access_requests.short_description = "Approve selected access requests"
    
    fieldsets = (
        ('Access Request', {
            'fields': ('user', 'investment', 'is_approved')
        }),
        ('Payment Information', {
            'fields': ('payment_reference', 'payment_proof', 'admin_notes')
        }),
        ('Approval Information', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Register models
admin.site.register(InvestmentPlan, InvestmentPlanAdmin)
admin.site.register(Investment, InvestmentAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(InvestmentAccess, InvestmentAccessAdmin)