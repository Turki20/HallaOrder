from datetime import timedelta, datetime
from decimal import Decimal
from itertools import combinations
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Max, Q, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate, ExtractHour, ExtractWeekDay, Coalesce

from users.decorators import restaurant_owner_required
from restaurants.models import Restaurant, Branch
from orders.models import Order, OrderItem, OrderStatus
from menu.models import Product

REVENUE_STATUSES = (OrderStatus.DELIVERED,)

def get_user_restaurant(user):
    try:
        return user.restaurants
    except (Restaurant.DoesNotExist, AttributeError):
        return None

def _parse_range(request):
    end = request.GET.get("end")
    start = request.GET.get("start")
    now = timezone.now()
    if start and end:
        s = datetime.fromisoformat(start).date()
        e = datetime.fromisoformat(end).date()
    else:
        e = now.date()
        s = e - timedelta(days=6 if request.GET.get("period") == "week" else 29)
    return s, e

def _paid_orders_qs(restaurant, start_date, end_date):
    return Order.objects.filter(
        branch__restaurant=restaurant,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status__in=REVENUE_STATUSES,
    )

def _line_revenue():
    return ExpressionWrapper(
        F("quantity") * F("product__price"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

@login_required
@restaurant_owner_required
def ai_view(request):
    restaurant = get_user_restaurant(request.user)
    branches = Branch.objects.filter(restaurant=restaurant) if restaurant else []
    period = request.GET.get("period", "week")
    context = {"branches": branches, "selected": {"period": period}, "current_page": "reports:ai"}
    return render(request, "reports/ai.html", context)

@login_required
@restaurant_owner_required
def insights_summary(request):
    r = get_user_restaurant(request.user)
    if not r:
        return JsonResponse({"kpi": {}, "top_product": None})
    s, e = _parse_range(request)
    qs = _paid_orders_qs(r, s, e)

    agg = qs.aggregate(
        revenue=Coalesce(Sum("total_price"), Decimal("0.00")),
        orders=Count("id"),
        aov=Coalesce(Avg("total_price"), Decimal("0.00")),
        last=Max("created_at"),
    )
    revenue = float(agg["revenue"] or 0)
    orders = int(agg["orders"] or 0)
    aov = float(agg["aov"] or 0)
    last_order = agg["last"].isoformat() if agg["last"] else None

    top = (
        OrderItem.objects.filter(order__in=qs)
        .values("product__name")
        .annotate(rev=Coalesce(Sum(_line_revenue()), Decimal("0.00")))
        .order_by("-rev")
        .first()
    )
    top_product = top["product__name"] if top else None

    return JsonResponse({"kpi": {"revenue": revenue, "orders": orders, "aov": aov, "last_order": last_order}, "top_product": top_product})

@login_required
@restaurant_owner_required
def reco_trending(request):
    r = get_user_restaurant(request.user)
    if not r:
        return JsonResponse({"items": []})
    s, e = _parse_range(request)
    data = (
        OrderItem.objects.filter(order__in=_paid_orders_qs(r, s, e))
        .values("product_id", "product__name")
        .annotate(qty=Coalesce(Sum("quantity"), 0), revenue=Coalesce(Sum(_line_revenue()), Decimal("0.00")))
        .order_by("-qty")[:12]
    )
    out = [{"id": d["product_id"], "name": d["product__name"], "qty": int(d["qty"] or 0)} for d in data]
    return JsonResponse({"items": out})

@login_required
@restaurant_owner_required
def product_search(request):
    r = get_user_restaurant(request.user)
    if not r:
        return JsonResponse({"results": []})
    q = (request.GET.get("q") or "").strip()
    pf = {f.name for f in Product._meta.get_fields()}
    qs = Product.objects.all()
    if "restaurant" in pf:
        qs = qs.filter(restaurant=r)
    elif "branch" in pf:
        qs = qs.filter(branch__restaurant=r)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(ar_name__icontains=q))
    results = list(qs.values("id", "name")[:20])
    if not results:
        s, e = _parse_range(request)
        oi = OrderItem.objects.filter(order__in=_paid_orders_qs(r, s, e))
        if q:
            oi = oi.filter(product__name__icontains=q)
        hits = oi.values("product_id", name=F("product__name")).order_by().distinct()[:20]
        results = [{"id": h["product_id"], "name": h["name"]} for h in hits]
    return JsonResponse({"results": results})

@login_required
@restaurant_owner_required
def reco_also_bought(request):
    r = get_user_restaurant(request.user)
    if not r:
        return JsonResponse({"items": []})
    s, e = _parse_range(request)
    raw = request.GET.get("product_ids", "")
    basket = [int(x) for x in raw.split(",") if x.strip().isdigit()]
    if not basket:
        return JsonResponse({"items": []})
    paid = _paid_orders_qs(r, s, e)
    orders_with_any = (
        OrderItem.objects.filter(order__in=paid, product_id__in=basket)
        .values_list("order_id", flat=True)
        .distinct()
    )
    others = (
        OrderItem.objects.filter(order_id__in=orders_with_any)
        .exclude(product_id__in=basket)
        .values("product_id", "product__name")
        .annotate(score=Count("order_id"))
        .order_by("-score")[:10]
    )
    out = [{"id": o["product_id"], "name": o["product__name"], "score": int(o["score"] or 0)} for o in others]
    return JsonResponse({"items": out})

@login_required
@restaurant_owner_required
def heatmap_time(request):
    r = get_user_restaurant(request.user)
    if not r:
        return JsonResponse({"grid": [], "hours": [], "weekdays": []})
    s, e = _parse_range(request)
    qs = (
        _paid_orders_qs(r, s, e)
        .annotate(h=ExtractHour("created_at"), wd=ExtractWeekDay("created_at"))
        .values("h", "wd")
        .annotate(rev=Coalesce(Sum("total_price"), Decimal("0.00")))
    )
    grid = [[0 for _ in range(24)] for _ in range(7)]
    for row in qs:
        h = int(row["h"] or 0)
        wd = (int(row["wd"] or 1) - 1) % 7
        grid[wd][h] = float(row["rev"] or 0)
    hours = [f"{h:02d}" for h in range(24)]
    weekdays = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    return JsonResponse({"grid": grid, "hours": hours, "weekdays": weekdays})

@login_required
@restaurant_owner_required
def branches_compare(request):
    r = get_user_restaurant(request.user)
    if not r:
        return JsonResponse({"rows": []})
    s, e = _parse_range(request)
    data = (
        _paid_orders_qs(r, s, e)
        .values("branch__id", "branch__name")
        .annotate(revenue=Coalesce(Sum("total_price"), Decimal("0.00")), orders=Count("id"), aov=Coalesce(Avg("total_price"), Decimal("0.00")))
        .order_by("-revenue")
    )
    rows = []
    for d in data:
        rows.append(
            {
                "id": d["branch__id"],
                "name": d["branch__name"],
                "revenue": float(d["revenue"] or 0),
                "orders": int(d["orders"] or 0),
                "aov": float(d["aov"] or 0),
            }
        )
    return JsonResponse({"rows": rows})

@login_required
@restaurant_owner_required
def products_abc(request):
    r = get_user_restaurant(request.user)
    if not r:
        return JsonResponse({"items": []})
    s, e = _parse_range(request)
    items = list(
        OrderItem.objects.filter(order__in=_paid_orders_qs(r, s, e))
        .values("product_id", "product__name")
        .annotate(qty=Coalesce(Sum("quantity"), 0), revenue=Coalesce(Sum(_line_revenue()), Decimal("0.00")))
        .order_by("-revenue")
    )
    total = sum(float(i["revenue"] or 0) for i in items) or 1.0
    cum = 0.0
    out = []
    for i in items:
        rev = float(i["revenue"] or 0)
        cum += rev
        share = cum / total
        bucket = "A" if share <= 0.8 else ("B" if share <= 0.95 else "C")
        out.append(
            {
                "id": i["product_id"],
                "name": i["product__name"],
                "revenue": round(rev, 2),
                "qty": int(i["qty"] or 0),
                "bucket": bucket,
                "cum_pct": round(share * 100, 1),
            }
        )
    return JsonResponse({"items": out})

@login_required
@restaurant_owner_required
def simulate_discount(request):
    r = get_user_restaurant(request.user)
    if not r:
        return JsonResponse({"result": None})
    s, e = _parse_range(request)
    try:
        pid = int(request.GET.get("product_id"))
    except Exception:
        return JsonResponse({"result": None})
    elasticity = float(request.GET.get("elasticity", -1.1))
    disc = max(0.0, min(float(request.GET.get("discount", 10.0)), 90.0)) / 100.0

    agg = (
        OrderItem.objects.filter(order__in=_paid_orders_qs(r, s, e), product_id=pid)
        .aggregate(qty=Coalesce(Sum("quantity"), 0), rev=Coalesce(Sum(_line_revenue()), Decimal("0.00")))
    )
    qty = float(agg["qty"] or 0)
    rev = float(agg["rev"] or 0)
    if qty == 0:
        return JsonResponse({"result": None})

    avg_price = rev / qty
    new_price = avg_price * (1 - disc)
    new_qty = qty * (1 - elasticity * disc)
    proj_rev = new_price * new_qty

    return JsonResponse(
        {
            "result": {
                "baseline_qty": round(qty, 2),
                "baseline_price": round(avg_price, 2),
                "baseline_rev": round(rev, 2),
                "new_price": round(new_price, 2),
                "projected_qty": round(new_qty, 2),
                "projected_rev": round(proj_rev, 2),
                "delta_rev_pct": round(((proj_rev - rev) / rev) * 100, 1) if rev else None,
            }
        }
    )
