from datetime import timedelta, datetime
from io import StringIO
import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Max
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from users.decorators import restaurant_owner_required
from restaurants.models import Restaurant, Branch
from orders.models import Order, OrderItem, OrderStatus
from .models import CustomerProfile

REVENUE_STATUSES = (OrderStatus.DELIVERED,)

def _get_restaurant(user):
    try:
        return user.restaurants
    except (Restaurant.DoesNotExist, AttributeError):
        return None

def _detect_customer_field():
    fields = {f.name for f in Order._meta.get_fields()}
    for cand in ("customer_id", "customer", "user_id", "user"):
        if cand in fields:
            return cand
    return None

def _parse_range(request):
    end = request.GET.get("end")
    start = request.GET.get("start")
    now = timezone.now().date()
    if start and end:
        s = datetime.fromisoformat(start).date()
        e = datetime.fromisoformat(end).date()
    else:
        e = now
        s = e - timedelta(days=29)
    return s, e

def _orders_qs(r, s, e):
    return Order.objects.filter(
        branch__restaurant=r,
        created_at__date__gte=s,
        created_at__date__lte=e,
        status__in=REVENUE_STATUSES,
    )

@login_required
@restaurant_owner_required
def customers_page(request):
    r = _get_restaurant(request.user)
    if not r:
        return render(request, "reports/customers.html", {"error": "لا يوجد مطعم مرتبط بحسابك."})
    return render(request, "reports/customers.html", {"current_page": "reports:customers"})

@login_required
@restaurant_owner_required
def customers_list(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"rows": [], "count": 0})
    s, e = _parse_range(request)
    cust_field = _detect_customer_field()
    if not cust_field:
        return JsonResponse({"rows": [], "count": 0})

    qs = _orders_qs(r, s, e)
    agg = (
        qs.values(cust_field)
          .annotate(
              orders=Count("id", distinct=True),
              amount=Sum("total_price"),
              last=Max("created_at"),
          )
          .order_by("-amount")
    )

    rows = []
    for a in agg:
        ext = str(a[cust_field])
        prof, _ = CustomerProfile.objects.get_or_create(restaurant=r, external_id=ext)
        prof.orders = int(a["orders"] or 0)
        prof.total_spent = float(a["amount"] or 0)
        prof.last_order_at = a["last"] or prof.last_order_at
        prof.save(update_fields=["orders", "total_spent", "last_order_at", "updated_at"])
        rows.append({
            "id": prof.id,
            "external_id": prof.external_id,
            "name": prof.name or f"عميل #{ext}",
            "phone": prof.phone or "",
            "email": prof.email or "",
            "orders": prof.orders,
            "amount": float(prof.total_spent or 0),
            "last": prof.last_order_at.isoformat() if prof.last_order_at else None,
            "tags": prof.tags or "",
            "blocked": prof.blocked,
        })

    q = (request.GET.get("q") or "").strip()
    if q:
        q_lower = q.lower()
        rows = [
            r0 for r0 in rows
            if q_lower in str(r0["external_id"]).lower()
            or q_lower in (r0["name"] or "").lower()
            or q_lower in (r0["phone"] or "").lower()
            or q_lower in (r0["email"] or "").lower()
        ]

    min_orders = request.GET.get("min_orders")
    if min_orders and min_orders.isdigit():
        rows = [r0 for r0 in rows if r0["orders"] >= int(min_orders)]

    return JsonResponse({"rows": rows, "count": len(rows)})

@login_required
@restaurant_owner_required
def customers_bulk_tag(request):
    r = _get_restaurant(request.user)
    ids_raw = request.GET.get("ids", "")
    tag = (request.GET.get("tag") or "").strip()
    if not (r and ids_raw and tag):
        return JsonResponse({"updated": 0})
    ids = [int(x) for x in ids_raw.split(",") if x.strip().isdigit()]
    updated = 0
    for prof in CustomerProfile.objects.filter(restaurant=r, id__in=ids):
        cur = (prof.tags or "").split(",")
        if tag not in [x.strip() for x in cur if x.strip()]:
            cur.append(tag)
        prof.tags = ",".join([x.strip() for x in cur if x.strip()])
        prof.save(update_fields=["tags", "updated_at"])
        updated += 1
    return JsonResponse({"updated": updated})

@login_required
@restaurant_owner_required
def customers_bulk_block(request):
    r = _get_restaurant(request.user)
    ids_raw = request.GET.get("ids", "")
    block = request.GET.get("block", "1") == "1"
    if not (r and ids_raw):
        return JsonResponse({"updated": 0})
    ids = [int(x) for x in ids_raw.split(",") if x.strip().isdigit()]
    updated = CustomerProfile.objects.filter(restaurant=r, id__in=ids).update(blocked=block)
    return JsonResponse({"updated": updated})

@login_required
@restaurant_owner_required
def customers_export_csv(request):
    r = _get_restaurant(request.user)
    s, e = _parse_range(request)
    if not r:
        return HttpResponse("", content_type="text/csv")

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "external_id", "name", "phone", "email", "orders", "total_spent", "last_order_at", "tags", "blocked"])

    qs = CustomerProfile.objects.filter(restaurant=r).order_by("-last_order_at")
    for c in qs:
        writer.writerow([
            c.id, c.external_id, c.name or "", c.phone or "", c.email or "",
            c.orders, float(c.total_spent or 0),
            c.last_order_at.isoformat() if c.last_order_at else "",
            c.tags or "", "yes" if c.blocked else "no"
        ])

    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="customers.csv"'
    return resp
