# orders/models.py
# orders/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from restaurants.models import Branch
from menu.models import Product
# -------- choices --------
class OrderStatus(models.TextChoices):
    NEW = "New", "New"
    PREPARING = "Preparing", "Preparing"
    READY = "Ready", "Ready"
    OUT_FOR_DELIVERY = "OutForDelivery", "Out for Delivery"
    DELIVERED = "Delivered", "Delivered"
    CANCELLED = "Cancelled", "Cancelled"


class PaymentMethod(models.TextChoices):
    CASH = "Cash", "Cash"
    ONLINE = "Online", "Online"

# -------- core models --------
class Order(models.Model):

        
        
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="orders"
    )
    # Branch lives in the restaurants app
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.NEW
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["branch", "status", "-created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Order #{self.pk} — {self.get_status_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # Product lives in the menu app
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    options = models.TextField(blank=True)  # store JSON string if you like
    addons  = models.TextField(blank=True)  # store JSON string if you like

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.order} / {self.product} × {self.quantity}"
