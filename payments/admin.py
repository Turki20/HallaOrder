from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "method", "status", "transaction_id", "created_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("transaction_id", "order__id", "order__customer__username", "order__customer__email")
