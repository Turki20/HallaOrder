from django.db import models
from orders.models import Order

class PaymentMethodGateway(models.TextChoices):
    MADA = "Mada", "Mada"
    APPLEPAY = "ApplePay", "ApplePay"
    VISA = "Visa", "Visa"
    CASH = "Cash", "Cash"

class PaymentStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    COMPLETED = "Completed", "Completed"
    FAILED = "Failed", "Failed"

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments" , null=True , blank=True)
    method = models.CharField(
        max_length=16,
        choices=PaymentMethodGateway.choices,
        default=PaymentMethodGateway.VISA,   # 👈 pick what you prefer (Visa/Cash)
    )
    status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,       # 👈 sensible default
    )
    transaction_id = models.CharField(max_length=255, blank=True)  # allow blank; optional: null=True
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.pk} – {self.method} – {self.status}"

