from django.contrib import admin
from .models import Payment, Invoice

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "method", "status", "transaction_id", "created_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("transaction_id", "order__id", "order__customer__username", "order__customer__email")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "customer_email", "total_amount", "compliance_status", "sent_via", "created_at")
    list_filter = ("compliance_status", "sent_via", "created_at")
    search_fields = ("order__id", "customer_email")
