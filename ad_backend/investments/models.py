# investments/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class InvestmentPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    daily_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Investment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    daily_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - {self.amount}"
    
    def calculate_daily_profit(self):
        daily_profit = (self.amount * self.plan.daily_interest_rate) / 100
        return daily_profit

class InvestmentAccess(models.Model):
    """Model to track investment access approvals"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investment_access_requests')
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='access_requests')
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_access_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    payment_proof = models.ImageField(upload_to='investment_payments/', blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'investment']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.investment.plan.name} - {'Approved' if self.is_approved else 'Pending'}"

# investments/models.py - Add these fields to Transaction if needed
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('profit', 'Profit'),
        ('bonus', 'Bonus'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Add these fields if you need them
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    withdrawal_method = models.CharField(max_length=50, blank=True, null=True, choices=(
        ('bank', 'Bank Transfer'),
        ('btc', 'Bitcoin'),
        ('eth', 'Ethereum'),
        ('usdt', 'USDT'),
    ))
    
    def save(self, *args, **kwargs):
        # Calculate net amount if fee is present
        if self.fee and self.amount:
            self.net_amount = self.amount - self.fee
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} - {self.status}"