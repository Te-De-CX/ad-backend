from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Task, UserTask
from investments.models import Transaction
import uuid


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'bronze_price', 'silver_price', 'gold_price', 'is_active')
    list_editable = ('bronze_price', 'silver_price', 'gold_price', 'is_active')

    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'video')
        }),
        ('Pricing', {
            'fields': ('bronze_price', 'silver_price', 'gold_price')
        }),
        ('Rewards', {
            'fields': ('bronze_reward', 'silver_reward', 'gold_reward')
        }),
        ('Settings', {
            'fields': ('requires_subscription', 'is_active')
        }),
    )


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'tier', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'tier')

    actions = ['approve_tasks', 'reject_tasks']

    def approve_tasks(self, request, queryset):
        for ut in queryset.filter(status='pending'):
            ut.status = 'completed'
            ut.completed_at = timezone.now()
            ut.save()

            Transaction.objects.create(
                user=ut.user,
                transaction_type='bonus',
                amount=ut.reward_amount,
                status='completed',
                reference=f"TASK_{ut.id}_{uuid.uuid4().hex[:8]}",
                description=f"{ut.task.title} reward ({ut.tier})"
            )

        self.message_user(request, "Tasks approved successfully")

    def reject_tasks(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, "Tasks rejected")