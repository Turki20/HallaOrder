from datetime import datetime, timedelta, time
from io import StringIO
import csv
import os, random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import (
    Sum, Count, Avg, Max, Value,
    DecimalField, FloatField, DateTimeField
)
from django.db.models.functions import Coalesce

from users.decorators import restaurant_owner_required
from restaurants.models import Restaurant, Branch
from orders.models import Order, OrderItem


def _detect_field(model, candidates):
    fields = {f.name for f in model._meta.get_fields()}
    for c in candidates:
        if c in fields:
            return c
    return None

def _total_field():
    return _detect_field(Order, ("total_price", "total", "grand_total", "amount", "price"))

def _created_field():
    return _detect_field(Order, ("created_at", "created", "ordered_at", "placed_at", "timestamp", "date"))

def _order_type_field():
    return _detect_field(Order, ("order_type", "type", "channel", "source", "mode"))

def _payment_field():
    return _detect_field(Order, ("payment_method", "pay_method", "payment", "method"))

def _customer_field():
    return _detect_field(Order, ("customer", "customer_id", "user", "user_id", "client", "client_id"))

AR_2_DB_OTYPE = {"محلي": "dine_in", "استلام": "pickup", "توصيل": "delivery"}
def _map_otype_value(v): return AR_2_DB_OTYPE.get(v, v)

def _order_type_label(order):
    f = _order_type_field()
    if f:
        val = getattr(order, f, None)
        return str(val) if val else "غير محدد"
    for flag, name in (("is_dine_in","محلي"),("is_pickup","استلام"),("is_delivery","توصيل")):
        if hasattr(order, flag) and getattr(order, flag):
            return name
    return "غير محدد"

def _get_restaurant(user):
    try:
        return user.restaurants
    except (Restaurant.DoesNotExist, AttributeError):
        pass
    return Restaurant.objects.first()

def _parse_range(request):
    end_s = request.GET.get("end")
    start_s = request.GET.get("start")
    today = timezone.now().date()
    if start_s and end_s:
        s = datetime.fromisoformat(start_s).date()
        e = datetime.fromisoformat(end_s).date()
    else:
        e = today
        s = e - timedelta(days=29)
    return s, e

def _base_orders_qs(r, s, e):
    created_f = _created_field() or "created_at"
    return Order.objects.filter(
        branch__restaurant=r,
        **{f"{created_f}__date__gte": s, f"{created_f}__date__lte": e},
    )

def _apply_branch(qs, request):
    branch_id = request.GET.get("branch")
    if branch_id:
        try:
            qs = qs.filter(branch_id=int(branch_id))
        except Exception:
            pass
    return qs

def _apply_otype(qs, request):
    otype = (request.GET.get("otype") or "").strip()
    if not otype:
        return qs, None
    f = _order_type_field()
    if f:
        return qs.filter(**{f: _map_otype_value(otype)}), None
    return qs, otype

def _zero_for_total():
    name = _total_field() or "total_price"
    try:
        fld = Order._meta.get_field(name)
        if isinstance(fld, DecimalField):
            max_d = getattr(fld, "max_digits", 12) or 12
            dec_p = getattr(fld, "decimal_places", 2) or 2
            return Value(0, output_field=DecimalField(max_digits=max_d, decimal_places=dec_p))
        elif isinstance(fld, FloatField):
            return Value(0.0, output_field=FloatField())
        else:
            return Value(0)
    except Exception:
        return Value(0.0, output_field=FloatField())

def _customer_related_model():
    cf = _customer_field()
    if not cf:
        return None, None
    try:
        fld = Order._meta.get_field(cf)
        model = getattr(fld, "remote_field", None) and fld.remote_field.model or None
        return cf, model
    except Exception:
        return cf, None

def _detect_from_names(model, candidates):
    if not model:
        return None
    names = {f.name for f in model._meta.get_fields()}
    for c in candidates:
        if c in names:
            return c
    return None


@login_required
@restaurant_owner_required
def sales_view(request):
    r = _get_restaurant(request.user)
    branches = Branch.objects.filter(restaurant=r).only("id","name") if r else []
    ctx = {"restaurant": r, "current_page": "reports:sales", "branches": branches}
    return render(request, "reports/sales.html", ctx)


@login_required
@restaurant_owner_required
def api_sales_summary(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"kpi":{"orders":0,"revenue":0.0,"avg":0.0,"returning":0}})
    s, e = _parse_range(request)
    qs = _apply_branch(_base_orders_qs(r, s, e), request)
    qs, otype_label = _apply_otype(qs, request)
    if otype_label:
        ids = [o.id for o in qs.only("id") if _order_type_label(o) == otype_label]
        qs = qs.filter(id__in=ids)
    total_f = _total_field() or "total_price"
    zero = _zero_for_total()
    agg = qs.aggregate(
        orders=Count("id"),
        revenue=Coalesce(Sum(total_f), zero),
        avg=Coalesce(Avg(total_f), zero),
    )
    cust_f = _customer_field()
    repeat_count = 0
    if cust_f:
        repeat_count = qs.values(cust_f).annotate(cnt=Count("id")).filter(cnt__gte=2).count()
    return JsonResponse({"kpi":{
        "orders": int(agg.get("orders") or 0),
        "revenue": float(agg.get("revenue") or 0),
        "avg": float(agg.get("avg") or 0),
        "returning": int(repeat_count or 0),
    }})

@login_required
@restaurant_owner_required
def api_sales_by_branch(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"labels":[],"values":[]})
    s, e = _parse_range(request)
    qs = _apply_branch(_base_orders_qs(r, s, e), request)
    qs, otype_label = _apply_otype(qs, request)
    if otype_label:
        ids = [o.id for o in qs.only("id") if _order_type_label(o) == otype_label]
        qs = qs.filter(id__in=ids)
    total_f = _total_field() or "total_price"
    zero = _zero_for_total()
    data = (
        qs.values("branch__name")
          .annotate(revenue=Coalesce(Sum(total_f), zero))
          .order_by("-revenue")
    )
    labels = [(d["branch__name"] or "-") for d in data]
    values = [float(d["revenue"] or 0) for d in data]
    return JsonResponse({"labels":labels,"values":values})

@login_required
@restaurant_owner_required
def api_sales_by_type(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"labels":[],"values":[]})
    s, e = _parse_range(request)
    base = _apply_branch(_base_orders_qs(r, s, e), request)
    total_f = _total_field() or "total_price"
    zero = _zero_for_total()
    f = _order_type_field()
    otype = (request.GET.get("otype") or "").strip()
    if f:
        qs = base.filter(**{f: _map_otype_value(otype)}) if otype else base
        data = (
            qs.values(f)
              .annotate(revenue=Coalesce(Sum(total_f), zero))
              .order_by("-revenue")
        )
        labels = [str(d[f] or "غير محدد") for d in data]
        values = [float(d["revenue"] or 0) for d in data]
    else:
        tmp = {}
        for o in base.only("id"):
            t = _order_type_label(o)
            tmp[t] = tmp.get(t, 0.0) + float(getattr(o, total_f, 0) or 0)
        items = sorted(tmp.items(), key=lambda kv: -kv[1])
        labels = [k for k,_ in items]
        values = [v for _,v in items]
        if otype:
            filt = [(k,v) for k,v in zip(labels,values) if k==otype]
            labels, values = ([filt[0][0]],[filt[0][1]]) if filt else ([],[])
    return JsonResponse({"labels":labels,"values":values})

@login_required
@restaurant_owner_required
def api_sales_list(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"rows":[]})
    s, e = _parse_range(request)
    qs = _apply_branch(_base_orders_qs(r, s, e).select_related("branch").order_by("-id"), request)
    qs, otype_label = _apply_otype(qs, request)
    if otype_label:
        ids = [o.id for o in qs.only("id") if _order_type_label(o) == otype_label]
        qs = qs.filter(id__in=ids)
    total_f  = _total_field() or "total_price"
    created_f = _created_field() or "created_at"
    pay_f    = _payment_field()
    cust_f   = _customer_field()
    rows = []
    for o in qs[:200]:
        customer_val = getattr(o, cust_f, None) if cust_f else None
        branch_name  = getattr(getattr(o, "branch", None), "name", "-")
        payment      = getattr(o, pay_f, None) if pay_f else None
        created_val  = getattr(o, created_f, None)
        rows.append({
            "id": o.id,
            "created": created_val.isoformat() if created_val else None,
            "customer": str(customer_val) if customer_val is not None else "-",
            "branch": branch_name or "-",
            "otype": _order_type_label(o),
            "payment": str(payment) if payment else "-",
            "total": float(getattr(o, total_f, 0) or 0),
        })
    return JsonResponse({"rows": rows})

@login_required
@restaurant_owner_required
def api_sales_export(request):
    r = _get_restaurant(request.user)
    if not r:
        return HttpResponse("", content_type="text/csv")
    s, e = _parse_range(request)
    qs = _apply_branch(_base_orders_qs(r, s, e).select_related("branch").order_by("-id"), request)
    qs, otype_label = _apply_otype(qs, request)
    if otype_label:
        ids = [o.id for o in qs.only("id") if _order_type_label(o) == otype_label]
        qs = qs.filter(id__in=ids)
    total_f  = _total_field() or "total_price"
    created_f = _created_field() or "created_at"
    pay_f    = _payment_field()
    cust_f   = _customer_field()
    buf = StringIO()
    w = csv.writer(buf)
    w.writerow(["order_id","date","customer","branch","type","payment","total"])
    for o in qs:
        customer_val = getattr(o, cust_f, None) if cust_f else None
        created_val  = getattr(o, created_f, None)
        w.writerow([
            o.id,
            created_val.isoformat() if created_val else "",
            str(customer_val) if customer_val is not None else "",
            getattr(getattr(o, "branch", None), "name", "") or "",
            _order_type_label(o),
            str(getattr(o, pay_f, "") if pay_f else ""),
            float(getattr(o, total_f, 0) or 0),
        ])
    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="sales.csv"'
    return resp


@login_required
@restaurant_owner_required
def api_growth_reengage(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"rows": []})
    days = int(request.GET.get("days") or 30)
    today = timezone.now().date()
    cutoff = today - timedelta(days=days)
    created_f = _created_field() or "created_at"
    total_f   = _total_field()   or "total_price"
    zero      = _zero_for_total()
    cust_f    = _customer_field()
    if not cust_f:
        return JsonResponse({"rows": []})
    base = Order.objects.filter(branch__restaurant=r)
    qs = base.values(cust_f).annotate(
        last=Max(created_f),
        orders=Count("id"),
        spent=Coalesce(Sum(total_f), zero),
    )
    try:
        fld = Order._meta.get_field(created_f)
    except Exception:
        fld = None
    if isinstance(fld, DateTimeField):
        qs = qs.filter(last__date__lte=cutoff)
    else:
        qs = qs.filter(last__lte=cutoff)
    data = qs.order_by("last")[:200]
    cf_name, CModel = _customer_related_model()
    name_f  = _detect_from_names(CModel, ("name", "full_name", "first_name", "username"))
    phone_f = _detect_from_names(CModel, ("phone", "mobile", "phone_number", "mobile_number"))
    rows = []
    id_list = [d[cust_f] for d in data]
    info_map = {}
    if CModel and (name_f or phone_f) and id_list:
        for obj in CModel.objects.filter(pk__in=id_list).only("id"):
            info_map[obj.pk] = {
                "name":  getattr(obj, name_f, None)  if name_f  else None,
                "phone": getattr(obj, phone_f, None) if phone_f else None,
            }
    for d in data:
        cid = d[cust_f]
        info = info_map.get(cid, {})
        last_dt = d["last"]
        rows.append({
            "id": cid,
            "name": info.get("name") or str(cid),
            "phone": info.get("phone") or None,
            "last": last_dt.isoformat() if last_dt else None,
            "orders": int(d["orders"] or 0),
            "spent": float(d["spent"] or 0),
        })
    return JsonResponse({"rows": rows})

@login_required
@restaurant_owner_required
def api_growth_top_customers(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"rows": []})
    s, e = _parse_range(request)
    created_f = _created_field() or "created_at"
    total_f   = _total_field()   or "total_price"
    zero      = _zero_for_total()
    cust_f    = _customer_field()
    if not cust_f:
        return JsonResponse({"rows": []})
    base = Order.objects.filter(
        branch__restaurant=r,
        **{f"{created_f}__date__gte": s, f"{created_f}__date__lte": e},
    )
    data = (
        base.values(cust_f)
            .annotate(orders=Count("id"),
                      spent=Coalesce(Sum(total_f), zero),
                      last=Max(created_f))
            .order_by("-spent")[:200]
    )
    cf_name, CModel = _customer_related_model()
    name_f  = _detect_from_names(CModel, ("name", "full_name", "first_name", "username"))
    phone_f = _detect_from_names(CModel, ("phone", "mobile", "phone_number", "mobile_number"))
    rows = []
    id_list = [d[cust_f] for d in data]
    info_map = {}
    if CModel and (name_f or phone_f) and id_list:
        for obj in CModel.objects.filter(pk__in=id_list).only("id"):
            info_map[obj.pk] = {
                "name":  getattr(obj, name_f, None)  if name_f  else None,
                "phone": getattr(obj, phone_f, None) if phone_f else None,
            }
    for d in data:
        cid = d[cust_f]
        info = info_map.get(cid, {})
        last_dt = d.get("last")
        rows.append({
            "id": cid,
            "name": info.get("name") or str(cid),
            "phone": info.get("phone") or None,
            "last": last_dt.isoformat() if last_dt else None,
            "orders": int(d["orders"] or 0),
            "spent": float(d["spent"] or 0),
        })
    return JsonResponse({"rows": rows})


@login_required
@restaurant_owner_required
def api_sales_debug(request):
    r = _get_restaurant(request.user)
    s, e = _parse_range(request)
    created_f = _created_field() or "created_at"
    total_f   = _total_field() or "total_price"
    base = Order.objects.filter(
        branch__restaurant=r,
        **{f"{created_f}__date__gte": s, f"{created_f}__date__lte": e},
    )
    after_branch = _apply_branch(base, request)
    after_branch, otype_label = _apply_otype(after_branch, request)
    rows = []
    for o in after_branch.select_related("branch").order_by("-id")[:3]:
        created_val = getattr(o, created_f, None)
        rows.append({
            "id": o.id,
            "created": created_val.isoformat() if created_val else None,
            "branch": getattr(getattr(o, "branch", None), "name", "-"),
            "otype": _order_type_label(o),
            "total": float(getattr(o, total_f, 0) or 0),
        })
    return JsonResponse({
        "restaurant": getattr(r, "name", None),
        "used_fields": {
            "created": _created_field(),
            "total": _total_field(),
            "otype": _order_type_field(),
            "payment": _payment_field(),
            "customer": _customer_field(),
        },
        "counts": {
            "in_date_range": base.count(),
            "after_branch_otype": after_branch.count(),
        },
        "range": {"start": str(s), "end": str(e)},
        "sample": rows,
    })

@login_required
@restaurant_owner_required
def api_sales_ping(request):
    r = _get_restaurant(request.user)
    s, e = _parse_range(request)
    created_f = _created_field() or "created_at"
    total_f   = _total_field() or "total_price"
    qs = Order.objects.filter(
        branch__restaurant=r,
        **{f"{created_f}__date__gte": s, f"{created_f}__date__lte": e},
    ).select_related("branch").order_by("-id")[:3]
    rows = []
    for o in qs:
        created_val = getattr(o, created_f, None)
        rows.append({
            "id": o.id,
            "created": created_val.isoformat() if created_val else None,
            "branch": getattr(getattr(o, "branch", None), "name", "-"),
            "otype": _order_type_label(o),
            "total": float(getattr(o, total_f, 0) or 0),
        })
    return JsonResponse({"rows": rows})


def _render_promo_template(name, rest_name, offer, style="friendly"):
    name = name or "عميلنا العزيز"
    offer = int(offer or 10)
    if style == "formal":
        variants = [
            f"مرحبًا {name}، يسعد {rest_name} تقديم خصم {offer}% على طلبك القادم اليوم فقط. نتشرّف بزيارتك 🌟",
            f"{name} الكريم، نقدّم لك خصمًا بقيمة {offer}% لدى {rest_name}. العرض ساري اليوم — أهلاً بك.",
            f"تحية طيبة {name}، خصم {offer}% بانتظارك في {rest_name}. نرحّب بك ونقدّر ثقتك."
        ]
    elif style == "playful":
        variants = [
            f"يا {name} وينك! 😍 خصم {offer}% من {rest_name} عالسريع؟ يلا نوّرنا اليوم!",
            f"{name} الغالي، معدتنا تسأل عنك 🤭 خذ {offer}% خصم وخلي الطعم يحكي!",
            f"صفها ووصلها 😋 {offer}% خصم في {rest_name} — جاهزين نخدمك!"
        ]
    else:
        variants = [
            f"أهلًا {name}! عندك خصم {offer}% في {rest_name} اليوم 🥳 يسعدنا نشوفك.",
            f"{name} العزيز، خصم {offer}% على طلبك القادم من {rest_name}. نستناك 🤗",
            f"ولعّها يا {name}! {offer}% خصم حصري من {rest_name} اليوم فقط 🔥"
        ]
    random.shuffle(variants)
    return variants[:3]

def _maybe_llm_rewrite(ar_messages, rest_name, style="friendly"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ar_messages
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = (
            "أعد صياغة الرسائل التالية بأسلوب عربي " +
            ("ودي واحترافي" if style=="friendly" else "رسمي مهذب" if style=="formal" else "مرح وخفيف") +
            f" مع الحفاظ على الفكرة والخصم واسم المطعم ({rest_name}). أعد إخراج كل رسالة في سطر مستقل:\n\n" +
            "\n".join(f"- {m}" for m in ar_messages)
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":"أنت كاتب محتوى عربي تسويقي."},
                      {"role":"user","content":prompt}],
            temperature=0.7,
        )
        text = resp.choices[0].message.content.strip()
        lines = [l.strip("-• ").strip() for l in text.split("\n") if l.strip()]
        return lines[:3] or ar_messages
    except Exception:
        return ar_messages

@login_required
@restaurant_owner_required
def api_ai_promo(request):
    rest_name = getattr(_get_restaurant(request.user), "name", "مطعمنا")
    offer = request.GET.get("offer") or "10"
    style = (request.GET.get("style") or "friendly").strip().lower()
    name  = request.GET.get("name")
    msgs = _render_promo_template(name, rest_name, offer, style=style)
    msgs = _maybe_llm_rewrite(msgs, rest_name, style=style)
    return JsonResponse({"messages": msgs})


def _segment_customers(request, kind="inactive"):
    r = _get_restaurant(request.user)
    if not r:
        return []
    created_f = _created_field() or "created_at"
    total_f   = _total_field()   or "total_price"
    zero      = _zero_for_total()
    cust_f    = _customer_field()
    if not cust_f:
        return []
    base = Order.objects.filter(branch__restaurant=r)
    if kind == "inactive":
        days = int(request.GET.get("days") or 30)
        cutoff = timezone.now().date() - timedelta(days=days)
        qs = (base.values(cust_f)
              .annotate(last=Max(created_f), orders=Count("id"), spent=Coalesce(Sum(total_f), zero)))
        try:
            fld = Order._meta.get_field(created_f)
        except Exception:
            fld = None
        qs = qs.filter(last__date__lte=cutoff) if isinstance(fld, DateTimeField) else qs.filter(last__lte=cutoff)
        data = qs.order_by("last")[:500]
    else:
        s, e = _parse_range(request)
        qs = (base.filter(**{f"{created_f}__date__gte": s, f"{created_f}__date__lte": e})
              .values(cust_f)
              .annotate(last=Max(created_f), orders=Count("id"), spent=Coalesce(Sum(total_f), zero))
              .order_by("-spent")[:500])
        data = qs
    cf_name, CModel = _customer_related_model()
    name_f  = _detect_from_names(CModel, ("name","full_name","first_name","username"))
    phone_f = _detect_from_names(CModel, ("phone","mobile","phone_number","mobile_number"))
    info_map = {}
    ids = [d[cust_f] for d in data]
    if CModel and (name_f or phone_f) and ids:
        for obj in CModel.objects.filter(pk__in=ids).only("id"):
            info_map[obj.pk] = {
                "name":  getattr(obj, name_f, None)  if name_f  else None,
                "phone": getattr(obj, phone_f, None) if phone_f else None,
            }
    rows = []
    for d in data:
        cid = d[cust_f]
        info = info_map.get(cid, {})
        last_dt = d.get("last")
        rows.append({
            "id": cid,
            "name": info.get("name") or str(cid),
            "phone": (info.get("phone") or "").replace(" ", ""),
            "last": last_dt.isoformat() if last_dt else None,
            "orders": int(d.get("orders") or 0),
            "spent": float(d.get("spent") or 0),
        })
    return rows

@login_required
@restaurant_owner_required
def api_marketing_whatsapp_csv(request):
    kind  = (request.GET.get("kind") or "inactive").strip().lower()
    offer = request.GET.get("offer") or "10"
    style = (request.GET.get("style") or "friendly").strip().lower()
    rest_name = getattr(_get_restaurant(request.user), "name", "مطعمنا")
    rows = _segment_customers(request, kind=kind)
    buf = StringIO()
    w = csv.writer(buf)
    w.writerow(["name","phone","message","wa_link"])
    for r in rows:
        msgs = _render_promo_template(r["name"], rest_name, offer, style=style)
        msg  = msgs[0]
        phone = r["phone"].replace("+","")
        wa = f"https://wa.me/{phone}?text={msg}"
        w.writerow([r["name"], r["phone"], msg, wa])
    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="whatsapp_{kind}.csv"'
    return resp


def _quantile_edges(values, q=5):
    if not values:
        return []
    arr = sorted(values)
    edges = []
    for i in range(1, q):
        k = int(round(i * len(arr) / q)) - 1
        k = max(0, min(k, len(arr)-1))
        edges.append(arr[k])
    return edges

def _score_by_edges(v, edges, reverse=False):
    if v is None:
        return 1
    rank = 1
    for e in edges:
        if (v <= e if reverse else v >= e):
            rank += 1
    return max(1, min(rank, 5))

def _rfm_label(r, f, m):
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 4 and f >= 3:
        return "Loyal"
    if r >= 3 and m >= 4:
        return "Big Spenders"
    if r <= 2 and f <= 2 and m <= 2:
        return "At Risk"
    if r >= 3 and f <= 2:
        return "New / Potential"
    return "Regular"

@login_required
@restaurant_owner_required
def api_ds_rfm(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"summary":{}, "rows":[]})
    end = timezone.now().date()
    start = end - timedelta(days=120)
    created_f = _created_field() or "created_at"
    total_f   = _total_field()   or "total_price"
    zero      = _zero_for_total()
    cust_f    = _customer_field()
    if not cust_f:
        return JsonResponse({"summary":{}, "rows":[]})
    base = Order.objects.filter(
        branch__restaurant=r,
        **{f"{created_f}__date__gte": start, f"{created_f}__date__lte": end},
    )
    from django.db.models import Max
    data = (base.values(cust_f)
                 .annotate(last=Max(created_f),
                           freq=Count("id"),
                           money=Coalesce(Sum(total_f), zero)))
    cf_name, CModel = _customer_related_model()
    name_f  = _detect_from_names(CModel, ("name","full_name","first_name","username"))
    phone_f = _detect_from_names(CModel, ("phone","mobile","phone_number","mobile_number"))
    info_map = {}
    ids = [d[cust_f] for d in data]
    if CModel and (name_f or phone_f) and ids:
        for obj in CModel.objects.filter(pk__in=ids).only("id"):
            info_map[obj.pk] = {
                "name":  getattr(obj, name_f, None)  if name_f  else None,
                "phone": getattr(obj, phone_f, None) if phone_f else None,
            }
    rows = []
    rec_days = []
    freqs = []
    monies = []
    for d in data:
        last_dt = d.get("last")
        rec = (end - last_dt.date()).days if last_dt else 999
        mon = float(d.get("money") or 0)
        frq = int(d.get("freq") or 0)
        rec_days.append(rec); freqs.append(frq); monies.append(mon)
        cid = d[cust_f]
        info = info_map.get(cid, {})
        rows.append({
            "id": cid,
            "name": info.get("name") or str(cid),
            "phone": (info.get("phone") or "").replace(" ", ""),
            "recency_days": rec,
            "frequency": frq,
            "monetary": mon,
        })
    eR = _quantile_edges(rec_days)
    eF = _quantile_edges(freqs)
    eM = _quantile_edges(monies)
    summary = {}
    for rrow in rows:
        r_score = _score_by_edges(rrow["recency_days"], eR, reverse=True)
        f_score = _score_by_edges(rrow["frequency"],   eF)
        m_score = _score_by_edges(rrow["monetary"],    eM)
        label = _rfm_label(r_score, f_score, m_score)
        rrow.update({"r":r_score,"f":f_score,"m":m_score,"label":label})
        summary[label] = summary.get(label, 0) + 1
    rows.sort(key=lambda x: (-x["m"], -x["f"], x["recency_days"]))
    return JsonResponse({"summary": summary, "rows": rows[:300]})


@login_required
@restaurant_owner_required
def api_growth_bundles(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"rows":[]})
    s, e = _parse_range(request)
    created_f = _created_field() or "created_at"
    items = (
        OrderItem.objects.filter(
            order__branch__restaurant=r,
            **{f"order__{created_f}__date__gte": s, f"order__{created_f}__date__lte": e},
        )
        .values("order_id","product__name")
        .annotate(qty=Sum("quantity"))
        .order_by()
    )
    by_order = {}
    for it in items:
        if not it["product__name"]:
            continue
        if (it["qty"] or 0) <= 0:
            continue
        by_order.setdefault(it["order_id"], set()).add(it["product__name"])
    pairs = {}
    for prods in by_order.values():
        lst = sorted(prods)
        n = len(lst)
        for i in range(n):
            for j in range(i+1, n):
                key = (lst[i], lst[j])
                pairs[key] = pairs.get(key, 0) + 1
    rows = [{"a":k[0], "b":k[1], "count":v} for k,v in pairs.items()]
    rows.sort(key=lambda x: -x["count"])
    return JsonResponse({"rows": rows[:20]})

@login_required
@restaurant_owner_required
def api_growth_best_times(request):
    r = _get_restaurant(request.user)
    if not r:
        return JsonResponse({"hours":{"labels":[],"values":[]},"weekdays":{"labels":[],"values":[]}})
    s, e = _parse_range(request)
    created_f = _created_field() or "created_at"
    total_f   = _total_field() or "total_price"
    qs = Order.objects.filter(
        branch__restaurant=r,
        **{f"{created_f}__date__gte": s, f"{created_f}__date__lte": e},
    ).values_list(created_f, total_f)
    hours = [0.0]*24
    week = [0.0]*7
    for dt, total in qs:
        if dt is None:
            continue
        if isinstance(dt, datetime):
            dtt = dt
        else:
            dtt = datetime.combine(dt, time(12,0))
        h = dtt.hour
        wd = dtt.weekday()
        val = float(total or 0)
        if 0 <= h <= 23:
            hours[h] += val
        if 0 <= wd <= 6:
            week[wd] += val
    wlabels = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
    hlabels = [str(i) for i in range(24)]
    return JsonResponse({"hours":{"labels":hlabels,"values":hours},"weekdays":{"labels":wlabels,"values":week}})
