from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order
from .models import Invoice
from users.models import Profile


@receiver(post_save, sender=Order)
def create_invoice_for_new_order(sender, instance: Order, created: bool, **kwargs):
    # تُنشئ فاتورة تلقائياً عند إنشاء Order جديد (مثلاً عبر لوحة الإدارة)
    if not created:
        return

    customer_email = ""
    customer_name = ""
    customer_phone = ""
    if instance.customer:
        user = instance.customer
        customer_email = user.email or ""
        customer_name = (user.get_full_name() or user.username or "").strip()
        try:
            profile = Profile.objects.get(user=user)
            customer_phone = profile.phone or ""
        except Profile.DoesNotExist:
            customer_phone = ""

    # تجنب إنشاء فاتورة مكررة لنفس الطلب
    if Invoice.objects.filter(order=instance).exists():
        return

    # إنشاء الفاتورة بقيم افتراضية مأخوذة من المستخدم/البروفايل
    Invoice.objects.create(
        order=instance,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        total_amount=instance.total_price,
        compliance_status=False,
        sent_via="Email",
    )


