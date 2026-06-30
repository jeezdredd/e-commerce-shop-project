from django.db import models

from orders.models import Order


class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_ERROR = "error"
    STATUS_CHOICES = [
        (STATUS_PENDING, "pending"),
        (STATUS_CONFIRMED, "confirmed"),
        (STATUS_ERROR, "error"),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments"
    )
    number = models.CharField(max_length=32)
    name = models.CharField(max_length=255, blank=True)
    month = models.CharField(max_length=2, blank=True)
    year = models.CharField(max_length=4, blank=True)
    code = models.CharField(max_length=3, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    error_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.pk} ({self.status})"
