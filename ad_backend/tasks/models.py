# tasks/models.py
from django.db import models
from django.conf import settings

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    requires_subscription = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class UserTask(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='user_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_proof = models.ImageField(upload_to='task_payments/', blank=True, null=True)
    completion_proof = models.ImageField(upload_to='task_completions/', blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.task.title} - {self.status}"
    
    class Meta:
        unique_together = ['user', 'task']