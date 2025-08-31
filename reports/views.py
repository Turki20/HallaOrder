# views.py
from datetime import timedelta
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from restaurants.models import Branch, Restaurant
from orders.models import Order, OrderItem, OrderStatus
from users.decorators import restaurant_owner_required

# نعدّد الحالات التي نعتبرها "إيراد" فعلاً
REVENUE_STATUSES = (OrderStatus.DELIVERED,)


def get_user_restaurant(user):
    """
    نحاول نجيب المطعم المرتبط بالمستخدم.
    عندك علاقة OneToOne: user.restaurants
    """
    try:
        return user.restaurants
    except Restaurant.DoesNotExist:
        return None
    except AttributeError:
        return None


@login_required
@restaurant_owner_required
def dashboard_view(request):
    # 1) نجيب المطعم حق المستخدم
    restaurant = get_user_restaurant(request.user)

    # لو ما فيه مطعم، نرجّع الصفحة بقيم فاضية عشان ما تنهار
    if restaurant is None:
        context = {
            "error": "لا يوجد مطعم مرتبط بحسابك.",
            "branches": [],
            "selected": {"period": "week", "branch": "all", "order_type": "all"},
            "kpi": {"total_sales": 0, "total_orders": 0, "avg_sales": 0, "top_product": "-"},
            "chart_labels": json.dumps([], ensure_ascii=False),
            "chart_data": json.dumps([], ensure_ascii=False),
        }
        return render(request, "reports/dashboard.html", context)

    # 2) نقرأ الفلاتر من الـ GET
    period = request.GET.get("period", "week")     # week أو month
    branch_id = request.GET.get("branch", "all")   # "all" أو رقم
    order_type = request.GET.get("order_type", "all")  # ما له أثر حالياً (موديل Order ما فيه order_type)

    # 3) نحدد المدة الزمنية
    now = timezone.now()
    if period == "month":
        start_date = now - timedelta(days=29)
    else:
        start_date = now - timedelta(days=6)

    # 4) نجيب الطلبات الخاصة بمطعمنا ضمن المدة
    orders = Order.objects.filter(
        branch__restaurant=restaurant,
        created_at__date__gte=start_date.date(),
        created_at__date__lte=now.date(),
        status__in=REVENUE_STATUSES,  # لو تبغى كل الحالات احذف هذا السطر
    )

    # 5) فلترة الفرع لو المستخدم اختار فرع معيّن
    if branch_id != "all":
        orders = orders.filter(branch_id=branch_id)

    # 6) حساب الـ KPI (إجمالي المبيعات، عدد الطلبات، متوسط الطلب)
    totals = orders.aggregate(
        total_sales=Sum("total_price"),
        total_orders=Count("id"),
        avg_sales=Avg("total_price"),
    )

    kpi = {
        "total_sales": float(totals["total_sales"] or 0),
        "total_orders": int(totals["total_orders"] or 0),
        "avg_sales": float(totals["avg_sales"] or 0),
    }

    # 7) أكثر منتج تم طلبه (بالكمية)
    top_item = (
        OrderItem.objects
        .filter(order__in=orders)
        .values("product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")
        .first()
    )
    if top_item:
        kpi["top_product"] = top_item["product__name"]
    else:
        kpi["top_product"] = "-"

    # 8) تجهيز بيانات الرسم البياني (المبيعات لكل يوم)
    #    أولاً: نجمع المبيعات بحسب اليوم
    daily_qs = (
        orders.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(day_sales=Sum("total_price"))
        .order_by("day")
    )

    # نحط النتائج في قاموس عشان نقدر نملأ الأيام الناقصة بصفر
    sales_by_day = {}
    for row in daily_qs:
        day_key = row["day"]
        amount = float(row["day_sales"] or 0)
        sales_by_day[day_key] = amount

    # نكوّن قائمة بكل الأيام ضمن المدة (start_date → now)
    total_days = (now.date() - start_date.date()).days + 1
    all_days_list = []
    for i in range(total_days):
        this_day = (start_date.date() + timedelta(days=i))
        all_days_list.append(this_day)

    # نحضّر labels و data
    labels = []
    data = []
    for d in all_days_list:
        labels.append(d.strftime("%Y-%m-%d"))
        data.append(sales_by_day.get(d, 0.0))

    # 9) تجهيز باقي البيانات للإرسال للواجهة
    branches = Branch.objects.filter(restaurant=restaurant)

    context = {
        "branches": branches,
        "current_page": "reports:dashboard",
        "selected": {
            "period": period,
            "branch": str(branch_id),
            "order_type": order_type,  # موجود للتوافق مستقبلاً
        },
        "kpi": kpi,
        "chart_labels": json.dumps(labels, ensure_ascii=False),
        "chart_data": json.dumps(data, ensure_ascii=False),
    }

    # 10) نعرض الصفحة
    return render(request, "reports/dashboard.html", context)
