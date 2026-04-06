# tasks/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Task, UserTask
from investments.models import Transaction
import uuid

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount_to_pay', 'reward_amount', 'requires_subscription', 'is_active', 'created_at')
    list_filter = ('requires_subscription', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('amount_to_pay', 'reward_amount', 'requires_subscription', 'is_active')
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description')
        }),
        ('Financial Settings', {
            'fields': ('amount_to_pay', 'reward_amount')
        }),
        ('Requirements', {
            'fields': ('requires_subscription', 'is_active')
        }),
    )

class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'status', 'started_at', 'completed_at', 'view_payment_proof', 'view_completion_proof')
    list_filter = ('status', 'started_at')
    search_fields = ('user__email', 'task__title')
    readonly_fields = ('started_at',)
    actions = ['approve_tasks', 'reject_tasks']
    
    def view_payment_proof(self, obj):
        if obj.payment_proof and hasattr(obj.payment_proof, 'url'):
            return format_html('<a href="{}" target="_blank">View Payment</a>', obj.payment_proof.url)
        return "No proof"
    view_payment_proof.short_description = "Payment Proof"
    
    def view_completion_proof(self, obj):
        if obj.completion_proof and hasattr(obj.completion_proof, 'url'):
            return format_html('<a href="{}" target="_blank">View Completion</a>', obj.completion_proof.url)
        return "No proof"
    view_completion_proof.short_description = "Completion Proof"
    
    def approve_tasks(self, request, queryset):
        for user_task in queryset.filter(status='pending'):
            user_task.status = 'completed'
            user_task.completed_at = timezone.now()
            user_task.save()
            
            # Create reward transaction
            Transaction.objects.create(
                user=user_task.user,
                transaction_type='bonus',
                amount=user_task.task.reward_amount,
                status='completed',
                reference=f"TASK_REWARD_{user_task.id}_{uuid.uuid4().hex[:8]}",
                description=f"Reward for completing task: {user_task.task.title}"
            )
        
        self.message_user(request, f'{queryset.count()} tasks approved and rewards credited.')
    approve_tasks.short_description = "Approve selected tasks"
    
    def reject_tasks(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='failed', admin_notes='Task rejected by admin')
        self.message_user(request, f'{updated} tasks rejected.')
    reject_tasks.short_description = "Reject selected tasks"
    
    fieldsets = (
        ('User & Task', {
            'fields': ('user', 'task', 'status')
        }),
        ('Proofs', {
            'fields': ('payment_proof', 'completion_proof')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
        ('Dates', {
            'fields': ('started_at', 'completed_at')
        }),
    )

# Register models
admin.site.register(Task, TaskAdmin)
admin.site.register(UserTask, UserTaskAdmin)