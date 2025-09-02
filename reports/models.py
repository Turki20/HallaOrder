from django.db import models
from restaurants.models import Restaurant

class CustomerProfile(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="customer_profiles")
    external_id = models.CharField(max_length=64)  # قيمة العميل كما تظهر في جدول Order (customer_id / user_id ...)
    name = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    city = models.CharField(max_length=64, blank=True, null=True)
    orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_order_at = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, default="")
    blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("restaurant", "external_id")
        ordering = ["-last_order_at"]

    def __str__(self):
        return f"{self.restaurant_id}:{self.external_id}"
