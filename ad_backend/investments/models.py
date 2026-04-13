from django.db import models
from django.conf import settings
from decimal import Decimal


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

    def calculate_total_return(self, amount):
        """Calculate total profit for given amount over duration"""
        daily = (Decimal(str(amount)) * self.daily_interest_rate) / 100
        return daily * self.duration_days


class Investment(models.Model):
    STATUS_CHOICES = (
        ('pending',   'Pending'),
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investments'
    )
    plan = models.ForeignKey(
        InvestmentPlan,
        on_delete=models.CASCADE,
        related_name='investments'
    )
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
        return (self.amount * self.plan.daily_interest_rate) / 100

    def save(self, *args, **kwargs):
        # Auto-calculate profits when activated
        if self.status == 'active' and self.daily_profit == 0:
            self.daily_profit = self.calculate_daily_profit()
            self.total_profit = self.daily_profit * self.plan.duration_days
        super().save(*args, **kwargs)


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit',    'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('profit',     'Profit'),
        ('bonus',      'Bonus'),
    )

    STATUS_CHOICES = (
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('completed',  'Completed'),
        ('failed',     'Failed'),
        ('cancelled',  'Cancelled'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    withdrawal_method = models.CharField(max_length=20, blank=True, null=True)
    withdrawal_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} - {self.status}"

    def save(self, *args, **kwargs):
        # Auto-calculate net amount for withdrawals
        if self.transaction_type == 'withdrawal' and self.net_amount == 0:
            self.fee = self.amount * Decimal('0.05')
            self.net_amount = self.amount - self.fee
        super().save(*args, **kwargs)