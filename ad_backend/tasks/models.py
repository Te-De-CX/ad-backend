# tasks/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    video = models.FileField(upload_to='tasks/videos/', blank=True, null=True)
    bronze_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    silver_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gold_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bronze_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    silver_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gold_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    requires_subscription = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class UserTask(models.Model):
    TIER_CHOICES = (
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
    )
    
    STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),
        ('pending_review', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='user_tasks')
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='bronze')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    payment_proof = models.ImageField(upload_to='task_payments/', blank=True, null=True)
    completion_proof = models.ImageField(upload_to='task_completions/', blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'task']
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.task.title} ({self.tier}) - {self.status}"
    
    @property
    def task_title(self):
        return self.task.title
    
    @property
    def task_description(self):
        return self.task.description
    
    @property
    def task_video_url(self):
        return self.task.video.url if self.task.video else None
    
    @property
    def reward_amount(self):
        if self.tier == 'bronze':
            return self.task.bronze_reward
        elif self.tier == 'silver':
            return self.task.silver_reward
        else:
            return self.task.gold_reward