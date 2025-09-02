from datetime import timedelta, datetime
from io import StringIO
import csv
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Max
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from users.decorators import restaurant_owner_required
from restaurants.models import Restaurant
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
    for cand in ("customer_id", "customer", "user_id", "user", "client_id", "client"):
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

def _tier_and_pct(orders:int):
    if orders >= 10:
        return "vip", 95
    if orders >= 5:
        return "reg", 70
    return "new", 25

def _digits_only(s):
    return ''.join(ch for ch in str(s or '') if ch.isdigit())

@login_required
@restaurant_owner_required
def customers_page(request):
    r = _get_restaurant(request.user)
    ctx = {"current_page": "reports:customers", "restaurant": r}
    if not r:
        ctx["error"] = "لا يوجد مطعم مرتبط بحسابك."
    return render(request, "reports/customers.html", ctx)

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
        tier, pct = _tier_and_pct(prof.orders)
        phone_digits = _digits_only(prof.phone)
        wa = f"https://wa.me/{phone_digits}?text={quote('مرحبًا 👋 — فريق HalaOrder')}" if phone_digits else ""
        tel = f"tel:{phone_digits}" if phone_digits else ""
        mailto = f"mailto:{prof.email}" if (prof.email or "").strip() else ""
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
            "tier": tier,
            "loyalty_pct": pct,
            "wa": wa, "tel": tel, "mailto": mailto,
        })
    q = (request.GET.get("q") or "").strip().lower()
    if q:
        rows = [r0 for r0 in rows if
                q in str(r0["external_id"]).lower()
                or q in (r0["name"] or "").lower()
                or q in (r0["phone"] or "").lower()
                or q in (r0["email"] or "").lower()]
    tier = (request.GET.get("tier") or "").strip().lower()
    if tier in {"new","reg","vip"}:
        rows = [r0 for r0 in rows if r0.get("tier")==tier]
    if request.GET.get("has_phone") == "1":
        rows = [r0 for r0 in rows if _digits_only(r0.get("phone"))]
    if request.GET.get("has_email") == "1":
        rows = [r0 for r0 in rows if (r0.get("email") or "").strip()]
    try:
        min_amount = float(request.GET.get("min_amount") or 0)
        rows = [r0 for r0 in rows if (r0.get("amount") or 0) >= min_amount]
    except: pass
    try:
        max_amount = float(request.GET.get("max_amount") or 0)
        if max_amount>0:
            rows = [r0 for r0 in rows if (r0.get("amount") or 0) <= max_amount]
    except: pass
    try:
        last_days = int(request.GET.get("last_days") or 0)
        if last_days>0:
            cutoff = timezone.now() - timedelta(days=last_days)
            rows = [r0 for r0 in rows if r0.get("last") and datetime.fromisoformat(r0["last"]) >= cutoff]
    except: pass
    tag = (request.GET.get("tag") or "").strip()
    if tag:
        rows = [r0 for r0 in rows if tag in (r0.get("tags") or "")]
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
    if not r:
        return HttpResponse("", content_type="text/csv")
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id","external_id","name","phone","email","orders","total_spent","last_order_at","tags"])
    qs = CustomerProfile.objects.filter(restaurant=r).order_by("-last_order_at")
    for c in qs:
        writer.writerow([
            c.id, c.external_id, c.name or "", c.phone or "", c.email or "",
            c.orders, float(c.total_spent or 0),
            c.last_order_at.isoformat() if c.last_order_at else "",
            c.tags or ""
        ])
    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="customers.csv"'
    return resp

@login_required
@restaurant_owner_required
def customer_orders_preview(request):
    r = _get_restaurant(request.user)
    ext = request.GET.get("external_id")
    if not (r and ext):
        return JsonResponse({"orders": []})
    s, e = _parse_range(request)
    cust_field = _detect_customer_field()
    if not cust_field:
        return JsonResponse({"orders": []})
    base = _orders_qs(r, s, e).filter(**{cust_field: ext}).order_by("-created_at")[:5]
    out = []
    for o in base:
        items = (OrderItem.objects.filter(order=o)
                 .values("product__name")
                 .annotate(qty=Sum("quantity"))
                 .order_by())
        out.append({
            "id": o.id,
            "at": o.created_at.isoformat(),
            "total": float(o.total_price or 0),
            "items": [{"name": it["product__name"], "qty": int(it["qty"] or 0)} for it in items]
        })
    return JsonResponse({"orders": out})

@login_required
@restaurant_owner_required
def customers_ai_tags(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"rows":[]})
    days = int(request.GET.get("days") or 120)
    max_tags = int(request.GET.get("max") or 5)
    cust_field = _detect_customer_field()
    if not cust_field:
        return JsonResponse({"rows":[]})
    end = timezone.now().date()
    start = end - timedelta(days=days)
    items = (OrderItem.objects.filter(
                order__branch__restaurant=r,
                **{f"order__created_at__date__gte": start, f"order__created_at__date__lte": end})
             .values(f"order__{cust_field}","product__name")
             .annotate(qty=Sum("quantity"))
             .order_by())
    kw = {
        "برجر":"يحب البرجر","برغر":"يحب البرجر","chicken":"دجاج","دجاج":"دجاج","beef":"لحم","لحم":"لحم",
        "بيتزا":"بيتزا","شاورما":"شاورما","قهوة":"قهوة","موكا":"قهوة","لاتيه":"قهوة","اسبريسو":"قهوة",
        "شاي":"شاي","حلويات":"حلويات","كيندر":"حلويات","كريب":"حلويات","وافل":"حلويات","باستا":"باستا",
        "سلطة":"سلطة","صوص":"صوص","حار":"سبايسي","سبايسي":"سبايسي","spicy":"سبايسي","مشروب":"مشروبات",
        "بيبسي":"مشروبات","كولا":"مشروبات","افطار":"فطور","فطور":"فطور"
    }
    score = {}
    for row in items:
        ext = str(row[f"order__{cust_field}"])
        name = (row["product__name"] or "").lower()
        score.setdefault(ext, {})
        for k,t in kw.items():
            if k.lower() in name:
                score[ext][t] = score[ext].get(t, 0) + int(row["qty"] or 1)
    profs = {p.external_id:p for p in CustomerProfile.objects.filter(restaurant=r)}
    rows = []
    for ext, m in score.items():
        top = sorted(m.items(), key=lambda kv: -kv[1])[:max_tags]
        tags = ",".join([k for k,_ in top])
        p = profs.get(str(ext))
        rows.append({
            "external_id": str(ext),
            "name": (p and p.name) or f"عميل #{ext}",
            "tags": tags
        })
    rows.sort(key=lambda x: x["name"])
    return JsonResponse({"rows": rows})

@login_required
@restaurant_owner_required
def customers_tags_apply_all(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"updated":0})
    mode = (request.GET.get("mode") or "append").lower()
    days = int(request.GET.get("days") or 120)
    max_tags = int(request.GET.get("max") or 5)
    req = request.GET.copy()
    req["days"] = str(days)
    req["max"] = str(max_tags)
    request.GET = req
    preview = customers_ai_tags(request).json().get("rows", [])
    updated = 0
    for row in preview:
        p = CustomerProfile.objects.filter(restaurant=r, external_id=row["external_id"]).first()
        if not p:
            continue
        if mode == "replace":
            p.tags = row["tags"]
        else:
            cur = [x.strip() for x in (p.tags or "").split(",") if x.strip()]
            new = [x.strip() for x in (row["tags"] or "").split(",") if x.strip()]
            merged = []
            seen = set()
            for t in cur + new:
                if t and t not in seen:
                    seen.add(t); merged.append(t)
            p.tags = ",".join(merged)
        p.save(update_fields=["tags","updated_at"])
        updated += 1
    return JsonResponse({"updated":updated})

@login_required
@restaurant_owner_required
def customers_find_duplicates(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"groups":[]})
    rows = CustomerProfile.objects.filter(restaurant=r)
    phone_map = {}
    email_map = {}
    for p in rows:
        ph = _digits_only(p.phone)
        if len(ph) >= 9:
            phone_map.setdefault(ph, []).append(p)
        em = (p.email or "").strip().lower()
        if em:
            email_map.setdefault(em, []).append(p)
    def pack(mapper, key_prefix):
        out = []
        for k, lst in mapper.items():
            if len(lst) <= 1:
                continue
            lst_sorted = sorted(lst, key=lambda x: (-int(x.orders or 0), -(x.total_spent or 0.0), x.id))
            master = lst_sorted[0]
            out.append({
                "key": f"{key_prefix}:{k}",
                "master": master.id,
                "ids": [x.id for x in lst_sorted],
                "names": [x.name or f"عميل #{x.external_id}" for x in lst_sorted],
                "phones": [x.phone or "" for x in lst_sorted],
                "emails": [x.email or "" for x in lst_sorted],
                "orders": [int(x.orders or 0) for x in lst_sorted],
                "spent": [float(x.total_spent or 0) for x in lst_sorted],
            })
        return out
    groups = pack(phone_map,"phone") + pack(email_map,"email")
    return JsonResponse({"groups":groups})

@login_required
@restaurant_owner_required
def customers_merge(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"merged":0})
    master_id = int(request.GET.get("master") or 0)
    ids_raw = (request.GET.get("ids") or "").strip()
    ids = [int(x) for x in ids_raw.split(",") if x.strip().isdigit()]
    ids = [i for i in ids if i != master_id]
    if not (master_id and ids):
        return JsonResponse({"merged":0})
    master = CustomerProfile.objects.filter(restaurant=r, id=master_id).first()
    if not master:
        return JsonResponse({"merged":0})
    merged = 0
    for p in CustomerProfile.objects.filter(restaurant=r, id__in=ids):
        master.orders = int(master.orders or 0) + int(p.orders or 0)
        master.total_spent = float(master.total_spent or 0) + float(p.total_spent or 0)
        if (p.last_order_at or None) and ((master.last_order_at or None) is None or p.last_order_at > master.last_order_at):
            master.last_order_at = p.last_order_at
        if not (master.name or "").strip() and (p.name or "").strip():
            master.name = p.name
        if not (master.phone or "").strip() and (p.phone or "").strip():
            master.phone = p.phone
        if not (master.email or "").strip() and (p.email or "").strip():
            master.email = p.email
        cur = [x.strip() for x in (master.tags or "").split(",") if x.strip()]
        new = [x.strip() for x in (p.tags or "").split(",") if x.strip()]
        tags = []
        seen = set()
        for t in cur + new:
            if t and t not in seen:
                seen.add(t); tags.append(t)
        master.tags = ",".join(tags)
        p.delete()
        merged += 1
    master.save(update_fields=["orders","total_spent","last_order_at","name","phone","email","tags","updated_at"])
    return JsonResponse({"merged":merged})
