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
    DELIVERY = 'delivery'
    PICKUP = 'pickup'
    DINE_IN = 'dine_in'

    ORDER_METHOD_CHOICES = [
        (DELIVERY, 'Delivery'),
        (PICKUP, 'Pickup'),
        (DINE_IN, 'Dine-in'),
    ]
    
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="orders"
    )
    
    guest_name = models.CharField(max_length=100, null=True, blank=True)
    guest_phone = models.CharField(max_length=15, null=True, blank=True)
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
    
    order_method = models.CharField(max_length=20, choices=ORDER_METHOD_CHOICES, null=True, blank=True)
    
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


class DeliveryDetails(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery_details')
    address = models.TextField()
    city = models.CharField(max_length=100)
    delivery_time = models.DateTimeField()

    def __str__(self):
        return f"Delivery to {self.address}"


class PickupDetails(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='pickup_details')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    pickup_time = models.DateTimeField()

    def __str__(self):
        return f"Pickup from {self.branch}"


class DineInDetails(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='dinein_details')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    number_of_people = models.IntegerField()
    reservation_time = models.DateTimeField()
    special_requests = models.TextField(blank=True)

    def __str__(self):
        return f"Dine-in for {self.number_of_people} people"
