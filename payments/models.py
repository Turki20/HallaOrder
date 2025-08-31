from django.db import models
# نماذج الدفع والفواتير الخاصة بتطبيق الدفع
from orders.models import Order

class PaymentMethodGateway(models.TextChoices):
    # طرق الدفع المتاحة لواجهة بوابة الدفع
    MADA = "Mada", "Mada"
    APPLEPAY = "ApplePay", "ApplePay"
    VISA = "Visa", "Visa"
    CASH = "Cash", "Cash"

class PaymentStatus(models.TextChoices):
    # حالات عملية الدفع
    PENDING = "Pending", "Pending"
    COMPLETED = "Completed", "Completed"
    FAILED = "Failed", "Failed"

class Payment(models.Model):
    # سجل دفع مرتبط بأمر شراء معيّن
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


# ---- Invoices ----
# نموذج الفاتورة لحفظ بيانات العميل وإجمالي الطلب وكيفية الإرسال
class InvoiceSentVia(models.TextChoices):
    EMAIL = "Email", "Email"
    SMS = "SMS", "SMS"


class Invoice(models.Model):
    # الفاتورة مرتبطة بـ Order واحد، وتضم بيانات العميل من نموذج السلة
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    compliance_status = models.BooleanField(default=False)
    sent_via = models.CharField(max_length=10, choices=InvoiceSentVia.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoices"
        indexes = [
            models.Index(fields=["order", "-created_at"]),
        ]

    def __str__(self):
        return f"Invoice #{self.pk} – Order #{self.order_id}"

