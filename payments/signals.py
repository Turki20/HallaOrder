from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db import transaction

from .models import Invoice


@receiver(post_save, sender=Invoice)
def send_invoice_email_on_create(sender, instance: Invoice, created: bool, **kwargs):
    if not created:
        return
    # لا ترسل إذا لم يتوفر بريد إلكتروني
    to_email = (instance.customer_email or '').strip()
    if not to_email:
        return

    invoice_pk = instance.pk
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@halaorder.local")

    def _send_after_commit():
        try:
            inv = Invoice.objects.select_related("order").get(pk=invoice_pk)
            order = inv.order
            items = list(getattr(order, "items", []).select_related("product").all()) if hasattr(order, "items") else []

            subject = f"فاتورة طلبك #{getattr(order, 'id', '')} - HalaOrder"
            context = {"invoice": inv, "order": order, "items": items}
            html_message = render_to_string("payments/email_invoice.html", context)
            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception:
            # لا نفشل العملية الأساسية بسبب خطأ في البريد
            pass

    transaction.on_commit(_send_after_commit)

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


