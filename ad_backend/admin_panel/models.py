# admin_panel/models.py
from django.db import models
from django.conf import settings

class AdminAction(models.Model):
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_actions')
    action_type = models.CharField(max_length=100)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='admin_actions_on_me')
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admin.email} - {self.action_type} - {self.created_at}"

class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key
    
    class Meta:
        verbose_name_plural = "System Settings"