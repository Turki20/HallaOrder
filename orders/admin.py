# orders/admin.py
from django.contrib import admin, messages
from .models import Order, OrderItem, OrderStatus, DineInDetails, DeliveryDetails, PickupDetails, PaymentMethod

# ---- Inlines ----
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    raw_id_fields = ("product",)  # faster than a huge dropdown
    fields = ("product", "quantity", "options", "addons")
    show_change_link = True


# ---- Actions ----
def _bulk_set_status(modeladmin, request, queryset, status_value, label):
    updated = queryset.update(status=status_value)
    messages.success(request, f"تم تحديث حالة {updated} طلب(ات) إلى «{label}».")

@admin.action(description="تعيين الحالة: جديد")
def set_status_new(modeladmin, request, queryset):
    _bulk_set_status(modeladmin, request, queryset, OrderStatus.NEW, "New")

@admin.action(description="تعيين الحالة: قيد التجهيز")
def set_status_preparing(modeladmin, request, queryset):
    _bulk_set_status(modeladmin, request, queryset, OrderStatus.PREPARING, "Preparing")

@admin.action(description="تعيين الحالة: جاهز")
def set_status_ready(modeladmin, request, queryset):
    _bulk_set_status(modeladmin, request, queryset, OrderStatus.READY, "Ready")

@admin.action(description="تعيين الحالة: تم التسليم")
def set_status_delivered(modeladmin, request, queryset):
    _bulk_set_status(modeladmin, request, queryset, OrderStatus.DELIVERED, "Delivered")

@admin.action(description="تعيين الحالة: ملغي")
def set_status_cancelled(modeladmin, request, queryset):
    _bulk_set_status(modeladmin, request, queryset, OrderStatus.CANCELLED, "Cancelled")


@admin.action(description="إعادة حساب المجموع من العناصر")
def recalc_total_from_items(modeladmin, request, queryset):
    total_updated = 0
    for order in queryset.prefetch_related("items__product"):
        total = 0
        for it in order.items.all():
            price = getattr(it.product, "price", 0) or 0
            qty = it.quantity or 0
            total += price * qty
        # NOTE: 
        if order.total_price != total:
            order.total_price = total
            order.save(update_fields=["total_price"])
            total_updated += 1
    messages.success(request, f"تم تحديث الإجمالي في {total_updated} طلب(ات).")


# ---- Order Admin ----
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]

    list_display = (
        "id", "branch", "customer", "status", "payment_method",
        "total_price", "created_at",
    )
    list_display_links = ("id",)
    list_editable = ("status", "payment_method", "total_price")
    list_filter = ("branch", "status", "payment_method", ("created_at", admin.DateFieldListFilter))
    search_fields = ("id", "customer__username", "customer__email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    actions = [
        set_status_new,
        set_status_preparing,
        set_status_ready,
        set_status_delivered,
        set_status_cancelled,
        recalc_total_from_items,
    ]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity")
    list_filter = ("order__branch",)
    search_fields = ("order__id", "product__name")
    raw_id_fields = ("order", "product")
    ordering = ("-id",)


admin.site.register(DeliveryDetails)
admin.site.register(DineInDetails)
# admin.site.register(PaymentMethod)
admin.site.register(PickupDetails)