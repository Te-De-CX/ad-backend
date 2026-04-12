from django.db import models
from django.conf import settings


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    video = models.FileField(upload_to='tasks/videos/', blank=True, null=True)

    # 🪙 Tier pricing
    bronze_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    silver_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gold_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # 💰 Tier rewards
    bronze_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    silver_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gold_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    requires_subscription = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    # 🔥 Always use these helpers instead of trusting frontend values
    def get_price(self, tier):
        return {
            "bronze": self.bronze_price,
            "silver": self.silver_price,
            "gold": self.gold_price,
        }.get(tier, 0)

    def get_reward(self, tier):
        return {
            "bronze": self.bronze_reward,
            "silver": self.silver_reward,
            "gold": self.gold_reward,
        }.get(tier, 0)


class UserTask(models.Model):

    STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),
        ('pending_review', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    TIER_CHOICES = (
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_tasks'
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='user_tasks'
    )

    tier = models.CharField(max_length=10, choices=TIER_CHOICES)

    # 🔥 IMPORTANT: status controls retries instead of DB constraints
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_payment'
    )

    payment_proof = models.ImageField(upload_to='task_payments/', blank=True, null=True)
    completion_proof = models.ImageField(upload_to='task_completions/', blank=True, null=True)

    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    admin_notes = models.TextField(blank=True, null=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # ❌ REMOVED unique_together
    # Reason: it prevented retries and caused "blocked" issues

    def __str__(self):
        return f"{self.user.email} - {self.task.title} ({self.tier})"

    def set_reward(self):
        self.reward_amount = self.task.get_reward(self.tier)