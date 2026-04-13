from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import InvestmentPlan, Investment, Transaction


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_amount', 'max_amount', 'daily_interest_rate', 'duration_days', 'is_active')
    list_filter = ('is_active',)
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


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'amount', 'daily_profit', 'total_profit', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'plan', 'created_at')
    search_fields = ('user__email', 'user__username', 'plan__name')
    readonly_fields = ('created_at', 'updated_at', 'daily_profit', 'total_profit')
    actions = ['approve_investments', 'complete_investments', 'cancel_investments']

    fieldsets = (
        ('User Information', {'fields': ('user',)}),
        ('Investment Details', {'fields': ('plan', 'amount', 'status')}),
        ('Profit Information', {'fields': ('daily_profit', 'total_profit')}),
        ('Dates', {'fields': ('start_date', 'end_date', 'created_at', 'updated_at')}),
    )

    def approve_investments(self, request, queryset):
        for inv in queryset.filter(status='pending'):
            inv.status = 'active'
            inv.start_date = timezone.now()
            inv.end_date = timezone.now() + timezone.timedelta(days=inv.plan.duration_days)
            inv.daily_profit = inv.calculate_daily_profit()
            inv.total_profit = inv.daily_profit * inv.plan.duration_days
            inv.save()
        self.message_user(request, "Selected investments approved and profits calculated.")
    approve_investments.short_description = "Approve → set Active + calculate profits"

    def complete_investments(self, request, queryset):
        queryset.filter(status='active').update(
            status='completed',
            end_date=timezone.now()
        )
        self.message_user(request, "Selected investments marked as completed.")
    complete_investments.short_description = "Mark selected investments as Completed"

    def cancel_investments(self, request, queryset):
        queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, "Selected investments cancelled.")
    cancel_investments.short_description = "Cancel selected investments"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'transaction_type', 'amount',
        'fee', 'net_amount', 'status', 'withdrawal_method',
        'reference', 'created_at'
    )
    list_filter = ('transaction_type', 'status', 'withdrawal_method', 'created_at')
    search_fields = ('user__email', 'reference', 'description', 'withdrawal_details')
    readonly_fields = ('created_at', 'updated_at', 'reference', 'fee', 'net_amount')
    actions = ['mark_processing', 'approve_transactions', 'reject_transactions']

    fieldsets = (
        ('Transaction Info', {
            'fields': ('user', 'transaction_type', 'amount', 'fee', 'net_amount', 'status', 'reference')
        }),
        ('Withdrawal Info', {
            'fields': ('withdrawal_method', 'withdrawal_details')
        }),
        ('Notes', {
            'fields': ('description', 'admin_notes')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def mark_processing(self, request, queryset):
        queryset.filter(status='pending').update(status='processing')
        self.message_user(request, "Transactions marked as Processing.")
    mark_processing.short_description = "Mark as Processing (payment being sent)"

    def approve_transactions(self, request, queryset):
        queryset.filter(status__in=['pending', 'processing']).update(status='completed')
        self.message_user(request, "Transactions approved and marked Completed.")
    approve_transactions.short_description = "Approve → mark as Completed"

    def reject_transactions(self, request, queryset):
        queryset.filter(status__in=['pending', 'processing']).update(status='failed')
        self.message_user(request, "Transactions rejected.")
    reject_transactions.short_description = "Reject selected transactions"