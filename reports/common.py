from datetime import timedelta, datetime
from decimal import Decimal

from django.utils import timezone
from django.db.models import F, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce

from restaurants.models import Restaurant
from orders.models import Order, OrderItem, OrderStatus

REVENUE_STATUSES = (OrderStatus.DELIVERED,)

def get_user_restaurant(user):
    try:
        return user.restaurants
    except (Restaurant.DoesNotExist, AttributeError):
        return None

def parse_range(request):
    end = request.GET.get("end")
    start = request.GET.get("start")
    now = timezone.now().date()
    if start and end:
        s = datetime.fromisoformat(start).date()
        e = datetime.fromisoformat(end).date()
    else:
        period = request.GET.get("period", "week")
        e = now
        s = e - timedelta(days=6 if period == "week" else 29)
    return s, e

def param_int(request, key):
    val = request.GET.get(key)
    try:
        return int(val) if val not in (None, "", "all") else None
    except ValueError:
        return None

def paid_orders_qs(restaurant, s, e, branch_id=None):
    qs = Order.objects.filter(
        branch__restaurant=restaurant,
        created_at__date__gte=s,
        created_at__date__lte=e,
        status__in=REVENUE_STATUSES,
    )
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    return qs

def line_revenue():
    names = {f.name for f in OrderItem._meta.get_fields()}
    if "total_price" in names:
        return F("total_price")
    unit = "unit_price" if "unit_price" in names else ("price" if "price" in names else None)
    qty  = "quantity" if "quantity" in names else ("qty" if "qty" in names else None)
    if unit and qty:
        return ExpressionWrapper(F(unit) * F(qty), output_field=DecimalField(max_digits=14, decimal_places=2))
    return ExpressionWrapper(F("quantity") * F("product__price"), output_field=DecimalField(max_digits=14, decimal_places=2))

def detect_customer_field():
    names = {f.name for f in Order._meta.get_fields()}
    for cand in ("customer_id", "customer", "user_id", "user", "client_id", "client"):
        if cand in names:
            return cand
    return None
