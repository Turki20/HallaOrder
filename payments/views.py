import json
from decimal import Decimal

import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token

from .models import Payment
from orders.models import Order  # مهم: نقرأ الطلب
from decimal import Decimal
from django.shortcuts import get_object_or_404
from orders.models import Order, OrderStatus  # ← use your models
# Stripe secret (test)
stripe.api_key = settings.STRIPE_SECRET_KEY
# payments/views.py (top)


ZERO_DECIMAL = {"jpy", "krw", "vnd"}  # SAR is NOT zero-decimal

def _to_smallest_unit(amount_riyal: Decimal, currency: str = "sar") -> int:
    if currency.lower() in ZERO_DECIMAL:
        return int(Decimal(amount_riyal).quantize(Decimal("1")))
    return int((Decimal(amount_riyal).quantize(Decimal("0.01"))) * 100)


def _smallest_unit(amount_decimal: Decimal, currency: str = "usd") -> int:
    # USD/SAR etc. → 2 decimals
    if amount_decimal is None:
        amount_decimal = Decimal("0.00")
    return int((amount_decimal.quantize(Decimal("0.01"))) * 100)

def _order_total(order: Order) -> Decimal:
    """
    1) Prefer order.total_price (matches your model)
    2) Fallback: sum product.price * quantity from items
    """
    if order.total_price and Decimal(order.total_price) > 0:
        return Decimal(order.total_price)

    s = Decimal("0.00")
    for it in order.items.select_related("product").all():
        price = Decimal(getattr(it.product, "price", 0) or 0)
        qty = int(getattr(it, "quantity", 1) or 1)
        s += price * qty
    return s


def _smallest_unit(amount_decimal: Decimal, currency: str = "usd") -> int:
    """
    يحوّل 10.50 إلى 1050 (cents). صالح لـ USD/SAR … إلخ (خانتين عشريتين).
    """
    if amount_decimal is None:
        amount_decimal = Decimal("0.00")
    return int((amount_decimal.quantize(Decimal("0.01"))) * 100)


def _order_total(order: Order) -> Decimal:
    """
    يقرأ الإجمالي من order.total_price (مطابق لهيكل الجداول اللي عطيتني).
    لو كان صفر/None يحاول fallback يحسب من المنتجات (اختياري).
    """
    total = getattr(order, "total_price", None)
    if total is not None and Decimal(total) > 0:
        return Decimal(total)

    # Fallback اختياري (لو تحتاج تجمع يدويًا من العناصر والمنتجات):
    items = getattr(order, "items", None)
    if items is not None:
        s = Decimal("0.00")
        for it in order.items.select_related("product").all():
            price = Decimal(getattr(it.product, "price", 0) or 0)
            qty = int(getattr(it, "quantity", 1) or 1)
            s += price * qty
        return s

    return Decimal("0.00")


def checkout(request):
    """
    Open as: /payments/checkout/?order_id=123&currency=usd
    Shows the real total from DB and passes order_id to JS.
    """
    get_token(request)
    currency = (request.GET.get("currency") or getattr(settings, "STRIPE_DEFAULT_CURRENCY", "sar")).lower()
    order_id = request.GET.get("order_id")

    amount_smallest = 1000   # fallback for display while testing
    display_total = Decimal(amount_smallest) / 100

    order = None
    if order_id:
        order = get_object_or_404(Order, pk=order_id)
        total = _order_total(order)
        amount_smallest = _smallest_unit(total, currency)
        display_total = total

    return render(
        request,
        "payments/checkout.html",
        {
            "amount": amount_smallest,                # smallest unit (debug/info)
            "display_total": display_total,           # user-friendly
            "currency": currency,
            "order_id": order_id or "",
            "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
        },
    )


def create_checkout_session(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        data = json.loads(request.body.decode()) if request.body else {}
    except Exception:
        data = {}

    order_id = data.get("order_id")
    currency = data.get("currency", "usd")
    if not order_id:
        return HttpResponseBadRequest("order_id is required")

    order = get_object_or_404(Order, pk=order_id)
    total = _order_total(order)
    amount_smallest = _smallest_unit(total, currency)

    product_name = f"Order #{order.id}"
    if hasattr(order, "branch") and getattr(order.branch, "restaurant", None):
        rest = getattr(order.branch.restaurant, "name", None)
        if rest:
            product_name = f"{rest} – Order #{order.id}"

    success_url = request.build_absolute_uri(reverse("payments:success")) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url  = request.build_absolute_uri(reverse("payments:cancel"))

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": currency,
                "product_data": {"name": product_name},
                "unit_amount": amount_smallest,
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"order_id": str(order.id)},
    )

    # Store a local Payment row (using your ERD fields)
    # transaction_id = Session ID for now (we’ll swap to PaymentIntent on success)
    from payments.models import Payment
    Payment.objects.create(
        order=order,
        method="Visa",             # test card path; adjust later via webhook if needed
        status="Pending",
        transaction_id=session.id,
    )

    return JsonResponse({"id": session.id})



def success(request):
    session_id = request.GET.get("session_id")
    status = None
    if session_id:
        session = stripe.checkout.Session.retrieve(session_id, expand=["payment_intent"])
        status = session.payment_status  # 'paid' or 'unpaid'
        pi = session.payment_intent.id if hasattr(session.payment_intent, "id") else session.payment_intent

        from payments.models import Payment
        p = Payment.objects.select_related("order").filter(transaction_id=session_id).first()
        if p:
            if status == "paid":
                p.status = "Completed"
                if pi:
                    p.transaction_id = pi
                p.save(update_fields=["status", "transaction_id"])
                if p.order:
                    p.order.status = OrderStatus.DELIVERED
                    p.order.save(update_fields=["status"])

    return render(request, "payments/success.html", {"session_id": session_id, "status": status})



def cancel(request):
    return render(request, "payments/cancel.html")


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

        from payments.models import Payment
        p = Payment.objects.select_related("order").filter(transaction_id=session_id).first()
        if p:
            p.status = "Completed"
            if payment_intent:
                p.transaction_id = payment_intent
            p.save(update_fields=["status", "transaction_id"])

            if p.order and hasattr(p.order, "status"):
                p.order.status = OrderStatus.DELIVERED  # or READY/PAID per your flow
                p.order.save(update_fields=["status"])

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        Payment.objects.filter(transaction_id=session.get("id")).update(status="Failed")

    elif event["type"] == "payment_intent.payment_failed":
        obj = event["data"]["object"]
        Payment.objects.filter(transaction_id=obj.get("id")).update(status="Failed")

    return HttpResponse(status=200)
