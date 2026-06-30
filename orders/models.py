from django.conf import settings
from django.db import models

from catalog.models import Product
from common.models import SoftDeleteModel


class DeliverySettings(models.Model):
    express_price = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    free_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    base_delivery_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=200
    )

    class Meta:
        verbose_name = "delivery settings"
        verbose_name_plural = "delivery settings"

    def __str__(self):
        return "Delivery settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Order(SoftDeleteModel):
    STATUS_NEW = "new"
    STATUS_ACCEPTED = "accepted"
    STATUS_PAID = "paid"
    STATUS_CHOICES = [
        (STATUS_NEW, "new"),
        (STATUS_ACCEPTED, "accepted"),
        (STATUS_PAID, "paid"),
    ]
    DELIVERY_ORDINARY = "ordinary"
    DELIVERY_EXPRESS = "express"
    DELIVERY_CHOICES = [
        (DELIVERY_ORDINARY, "ordinary"),
        (DELIVERY_EXPRESS, "express"),
    ]
    PAYMENT_ONLINE = "online"
    PAYMENT_SOMEONE = "someone"
    PAYMENT_CHOICES = [
        (PAYMENT_ONLINE, "online card"),
        (PAYMENT_SOMEONE, "someone account"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    delivery_type = models.CharField(
        max_length=20, choices=DELIVERY_CHOICES, default=DELIVERY_ORDINARY
    )
    payment_type = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_ONLINE
    )
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW
    )
    city = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=500, blank=True)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk}"

    def products_cost(self):
        return sum((item.price * item.count for item in self.items.all()), 0)

    def delivery_cost(self):
        cfg = DeliverySettings.load()
        if self.delivery_type == self.DELIVERY_EXPRESS:
            return cfg.express_price
        if self.products_cost() < cfg.free_threshold:
            return cfg.base_delivery_price
        return 0

    def recalculate_total(self):
        self.total_cost = self.products_cost() + self.delivery_cost()
        return self.total_cost


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    count = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product} x{self.count}"
