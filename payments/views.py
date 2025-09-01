import json
from decimal import Decimal

import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token

from .models import Payment, Invoice
# نماذج الطلبات والفروع والمنتجات
from websites.models import Website
from restaurants.models import Branch
from menu.models import Product
from orders.models import Order, OrderStatus, OrderItem, PaymentMethod
from .models import Invoice
from django.db.models import Q
from django.utils.http import urlencode

# إعداد مفتاح Stripe السري
stripe.api_key = settings.STRIPE_SECRET_KEY

# =============================
# توابع مساعدة للقيَم المالية
# =============================

ZERO_DECIMAL = {"jpy", "krw", "vnd"}  # عملات بلا كسور (SAR ليست ضمنها)

def _to_smallest_unit(amount_riyal: Decimal, currency: str = "sar") -> int:
    """تحويل 10.50 ريـال إلى 1050 (هللات) عند إنشاء جلسة الدفع."""
    if currency.lower() in ZERO_DECIMAL:
        return int(Decimal(amount_riyal).quantize(Decimal("1")))
    return int((Decimal(amount_riyal).quantize(Decimal("0.01"))) * 100)


def _smallest_unit(amount_decimal: Decimal, currency: str = "usd") -> int:
    """محول عام إلى أصغر وحدة (2 مراتب عشرية لمعظم العملات)."""
    if amount_decimal is None:
        amount_decimal = Decimal("0.00")
    return int((amount_decimal.quantize(Decimal("0.01"))) * 100)


def _order_total(order: Order) -> Decimal:
    """قراءة إجمالي الطلب من الحقل، أو حسابه من العناصر عند الحاجة."""
    if order.total_price and Decimal(order.total_price) > 0:
        return Decimal(order.total_price)
    s = Decimal("0.00")
    for it in order.items.select_related("product").all():
        price = Decimal(getattr(it.product, "price", 0) or 0)
        qty = int(getattr(it, "quantity", 1) or 1)
        s += price * qty
    return s

"""
مسارات الدفع المستخدمة فعليًا:
 - quick_checkout: إنشاء جلسة Stripe مباشرة من إجمالي معروف
 - success/cancel: الرجوع من Stripe وإنشاء الطلب/الفاتورة
 - stripe_webhook: تأكيد الحالة من Stripe
تمت إزالة مسارات تجريبية غير مستخدمة (checkout/create_checkout_session) لتبسيط التطبيق.
"""


# نجاح الدفع: إنشاء طلب من السلة (إن لم يكن موجودًا) ثم عرض الفاتورة

def success(request):
    session_id = request.GET.get("session_id")
    slug = request.GET.get("slug") or request.session.get("last_cart_slug")
    order_for_invoice = None
    status = None

    # قراءة حالة الجلسة من Stripe وتحديث سجل الدفع إن وجد
    if session_id:
        session = stripe.checkout.Session.retrieve(session_id, expand=["payment_intent"])
        status = session.payment_status  # 'paid' or 'unpaid'
        pi = session.payment_intent.id if hasattr(session.payment_intent, "id") else session.payment_intent

        p = Payment.objects.select_related("order").filter(transaction_id=session_id).first()
        if p and status == "paid":
            p.status = "Completed"
            if pi:
                p.transaction_id = pi
            p.save(update_fields=["status", "transaction_id"])
            if p.order:
                p.order.status = OrderStatus.DELIVERED
                p.order.save(update_fields=["status"])

    if status == "paid":
        # لو كان لدينا Order تم إنشاؤه مسبقًا في نفس الجلسة، نستخدمه
        last_order_id = request.session.get("last_order_id")
        if last_order_id:
            order_for_invoice = (
                Order.objects.select_related("branch").prefetch_related("items__product").filter(pk=last_order_id).first()
            )

        # وإلا ننشئ Order جديد من عناصر السلة المحفوظة في Session
        if not order_for_invoice and slug:
            website = Website.objects.select_related("restaurant").filter(slug=slug).first()
            if website:
                cart = request.session.get(f"cart_{website.id}", [])
                subtotal = sum((Decimal(str(i.get("price", 0))) * int(i.get("qty", 1) or 1)) for i in cart)
                tax = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
                total = (subtotal + tax).quantize(Decimal("0.01"))

                # اختيار فرع مناسب (أول فرع)
                branch = Branch.objects.filter(restaurant=website.restaurant).order_by("id").first() or Branch.objects.order_by("id").first()
                if branch:
                    created_order = Order.objects.create(
                        customer=request.user if request.user.is_authenticated else None,
                        branch=branch,
                        status=OrderStatus.NEW,
                        total_price=total,
                        payment_method=PaymentMethod.ONLINE,
                    )
                    for i in cart:
                        try:
                            product = Product.objects.filter(pk=int(i.get("id"))).first()
                        except Exception:
                            product = None
                        qty = int(i.get("qty", 1) or 1)
                        if product and qty > 0:
                            OrderItem.objects.create(
                                order=created_order,
                                product=product,
                                quantity=qty,
                                options=(i.get("size") or ""),
                                addons=",".join(i.get("addons", []) or []),
                            )
                    # تفريغ السلة وتخزين رقم الطلب لعرضه مباشرة
                    request.session[f"cart_{website.id}"] = []
                    request.session["last_order_id"] = created_order.id
                    request.session.modified = True

                    # إنشاء الفاتورة باستخدام بيانات الاسم والجوال المحفوظة من صفحة السلة
                    meta = request.session.get(f"cart_meta_{website.id}", {"name": "", "phone": "", "notes": ""})
                    try:
                        # احصل على الفاتورة إن كانت الإشارة قد أنشأتها مسبقًا، أو أنشئ واحدة جديدة
                        invoice, inv_created = Invoice.objects.get_or_create(
                            order=created_order,
                            defaults={
                                "customer_name": (meta.get("name") or "").strip(),
                                "customer_phone": (meta.get("phone") or "").strip(),
                                "customer_email": (request.user.email if request.user.is_authenticated else ""),
                                "total_amount": created_order.total_price,
                                "compliance_status": False,
                                "sent_via": "Email",
                            }
                        )
                        if not inv_created:
                            # حدث موجود: حدّث البيانات القادمة من النموذج لتظهر في التفاصيل
                            changed = False
                            name = (meta.get("name") or "").strip()
                            phone = (meta.get("phone") or "").strip()
                            email = (request.user.email if request.user.is_authenticated else "")
                            if name and invoice.customer_name != name:
                                invoice.customer_name = name; changed = True
                            if phone and invoice.customer_phone != phone:
                                invoice.customer_phone = phone; changed = True
                            if email and invoice.customer_email != email:
                                invoice.customer_email = email; changed = True
                            if invoice.total_amount != created_order.total_price:
                                invoice.total_amount = created_order.total_price; changed = True
                            if changed:
                                invoice.save()
                    except Exception:
                        # لا نمنع إكمال العملية إذا فشلت الفاتورة لأي سبب
                        pass
                    order_for_invoice = created_order

    if order_for_invoice:
        return render(request, "payments/invoice.html", {"order": order_for_invoice, "slug": slug})

    # في حال لم يتم الدفع أو حدث خطأ نعرض صفحة نجاح بسيطة
    return render(request, "payments/success.html", {"session_id": session_id, "status": status, "slug": slug})


def last_invoice(request: HttpRequest):
    """اعرض آخر فاتورة للعميل بناءً على رقم الطلب المخزن في الـ Session.
    إذا توفّر slug نعيد استخدامه لتقديم روابط الرجوع الصحيحة.
    """
    last_order_id = request.session.get("last_order_id")
    slug = request.GET.get("slug") or request.session.get("last_cart_slug")
    if not last_order_id:
        # لا توجد فاتورة حديثة
        if slug:
            return redirect("websites:menu", slug=slug)
        return HttpResponse("لا توجد فاتورة حديثة.", status=404)

    order = (
        Order.objects.select_related("branch").prefetch_related("items__product").filter(pk=last_order_id).first()
    )
    if not order:
        if slug:
            return redirect("websites:menu", slug=slug)
        return HttpResponse("الطلب غير موجود.", status=404)

    return render(request, "payments/invoice.html", {"order": order, "slug": slug})


# الإلغاء: الرجوع إلى سلة الموقع الصحيح

def cancel(request):
    slug = request.GET.get("slug") or request.session.get("last_cart_slug")
    if slug:
        return redirect(reverse("websites:cart", kwargs={"slug": slug}))
    return render(request, "payments/cancel.html")


# Webhook خاص بـ Stripe للتأكد من حالة الدفع (اختياري)
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

    if not endpoint_secret:
        return HttpResponse(status=200)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponseBadRequest("Invalid payload")
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")
        payment_intent = session.get("payment_intent")

        p = Payment.objects.select_related("order").filter(transaction_id=session_id).first()
        if p:
            p.status = "Completed"
            if payment_intent:
                p.transaction_id = payment_intent
            p.save(update_fields=["status", "transaction_id"])

            if p.order and hasattr(p.order, "status"):
                p.order.status = OrderStatus.DELIVERED
                p.order.save(update_fields=["status"])

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        Payment.objects.filter(transaction_id=session.get("id")).update(status="Failed")

    elif event["type"] == "payment_intent.payment_failed":
        obj = event["data"]["object"]
        Payment.objects.filter(transaction_id=obj.get("id")).update(status="Failed")

    return HttpResponse(status=200)


# الدفع السريع: نُنشئ جلسة Stripe مباشرة من الإجمالي ونحوّل المستخدم إلى Stripe

def quick_checkout(request):
    try:
        amount = Decimal(request.GET.get("amount", "0"))
    except Exception:
        amount = Decimal("0")
    currency = (request.GET.get("currency") or getattr(settings, "STRIPE_DEFAULT_CURRENCY", "sar")).lower()
    slug = request.GET.get("slug")

    amount_smallest = _smallest_unit(amount, currency)
    success_url = request.build_absolute_uri(reverse("payments:success")) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url  = request.build_absolute_uri(reverse("payments:cancel"))
    if slug:
        success_url = f"{success_url}&slug={slug}"
        cancel_url = f"{cancel_url}?slug={slug}"

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": currency,
                "product_data": {"name": "HalaOrder"},
                "unit_amount": amount_smallest,
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return redirect(session.url, permanent=False)


# نقطة API بسيطة لإرجاع حالة الطلب (يُستخدم في تحديث صفحة الفاتورة)

def public_order_status(request, order_id: int):
    order = Order.objects.filter(pk=order_id).first()
    if not order:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)
    return JsonResponse({
        "ok": True,
        "status": order.status,
        "status_display": order.get_status_display(),
        "updated_at": order.updated_at.isoformat(),
    })



def invoices_dashboard(request:HttpRequest):
    invoices = Invoice.objects.all().order_by("-created_at") # عدلها عشان يصير الواتير الخاصه بكل مطعم

    query = None
    sent_via_filter = None
    compliance_filter = None

    if request.method == "POST":
        query = request.POST.get("q")
        sent_via_filter = request.POST.get("sent_via")
        compliance_filter = request.POST.get("compliance_status")

        if query:
            invoices = invoices.filter(
                Q(customer_name__icontains=query) |
                Q(customer_email__icontains=query)
            )

        if sent_via_filter:
            invoices = invoices.filter(sent_via=sent_via_filter)

        if compliance_filter in ["true", "false"]:
            invoices = invoices.filter(compliance_status=(compliance_filter == "true"))

    context = {
        "invoices": invoices,
        "query": query,
        "sent_via_filter": sent_via_filter,
        "compliance_filter": compliance_filter,
    }
    return render(request, 'payments/invoices_dashboard.html', context)