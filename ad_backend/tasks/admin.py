from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Task, UserTask
from investments.models import Transaction
import uuid


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'bronze_price', 'silver_price', 'gold_price', 'is_active', 'video_preview')
    list_editable = ('bronze_price', 'silver_price', 'gold_price', 'is_active')
    search_fields = ('title',)
    ordering = ('-created_at',)

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

    def video_preview(self, obj):
        if obj.video:
            return format_html(
                '<video width="120" height="70" controls>'
                '<source src="{}" type="video/mp4">'
                '</video>',
                obj.video.url
            )
        return '—'
    video_preview.short_description = 'Preview'


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'task', 'tier', 'status',
        'reward_amount', 'payment_proof_preview',
        'started_at', 'completed_at'
    )
    list_filter = ('status', 'tier', 'task')
    search_fields = ('user__email', 'task__title')
    ordering = ('-started_at',)
    readonly_fields = ('started_at', 'reward_amount', 'payment_proof_preview', 'completion_proof_preview')

    actions = ['approve_payment', 'approve_completion', 'reject_tasks']

    def payment_proof_preview(self, obj):
        if obj.payment_proof:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="80" height="60" style="object-fit:cover;border-radius:4px"/>'
                '</a>',
                obj.payment_proof.url,
                obj.payment_proof.url,
            )
        return '—'
    payment_proof_preview.short_description = 'Payment Proof'

    def completion_proof_preview(self, obj):
        if obj.completion_proof:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="80" height="60" style="object-fit:cover;border-radius:4px"/>'
                '</a>',
                obj.completion_proof.url,
                obj.completion_proof.url,
            )
        return '—'
    completion_proof_preview.short_description = 'Completion Proof'

    # ← FIX: was filtering 'pending' but status is 'pending_review'
    def approve_payment(self, request, queryset):
        """Approve payment — move from pending_review to in_progress"""
        updated = queryset.filter(status='pending_review').update(status='in_progress')
        self.message_user(request, f"{updated} payment(s) approved. Users can now participate.")
    approve_payment.short_description = 'Approve payment → set In Progress'

    def approve_completion(self, request, queryset):
        """Approve completion — move from pending_review to completed and credit reward"""
        for ut in queryset.filter(status='pending_review'):
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
        self.message_user(request, "Tasks completed and rewards credited.")
    approve_completion.short_description = 'Approve completion → credit reward'

    def reject_tasks(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, "Tasks rejected.")
    reject_tasks.short_description = 'Reject selected tasks'